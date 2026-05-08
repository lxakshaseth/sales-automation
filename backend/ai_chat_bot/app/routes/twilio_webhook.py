from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from app.agents.main_agent import run_agent
from app.config.settings import settings
from app.core.logger import log_error, log_event, log_info
from app.core.rate_limiter import RateLimitError, check_rate_limit
from app.services.ai_media_processor import prepare_media_context
from app.services.conversation_service import record_assistant_message, record_message_received
from app.services.groq_service import GroqServiceError, generate_sales_reply
from app.services.language_service import detect_language
from app.services.twilio_service import build_twiml_response
from app.services.whatsapp_cloud_service import (
    WhatsAppCloudError,
    parse_incoming_messages,
    read_json_body,
    send_text_message,
    verify_meta_signature,
    verify_webhook_token,
)
from app.services.whatsapp_media_service import WhatsAppMediaError, process_all_twilio_media
from app.utils.twilio_parser import InvalidTwilioPayloadError, parse_twilio_form

router = APIRouter()


@router.get("/webhook")
async def whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    challenge = verify_webhook_token(
        hub_mode,
        hub_verify_token,
        hub_challenge,
        settings.whatsapp_verify_token,
    )
    if challenge is None:
        log_error("WhatsApp webhook verification failed", mode=hub_mode)
        raise HTTPException(status_code=403, detail="verification failed")
    log_event("whatsapp_webhook_verified")
    return PlainTextResponse(challenge)


@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        return await _legacy_twilio_webhook(request)

    try:
        raw_body, payload = await read_json_body(request)
    except WhatsAppCloudError as exc:
        log_error("Invalid WhatsApp Cloud webhook payload", error=str(exc))
        return JSONResponse({"success": False, "error": "invalid payload"}, status_code=400)

    if not verify_meta_signature(raw_body, request.headers.get("x-hub-signature-256")):
        log_error("WhatsApp webhook signature verification failed")
        return JSONResponse({"success": False, "error": "invalid signature"}, status_code=403)

    incoming_messages = parse_incoming_messages(payload)
    for incoming in incoming_messages:
        background_tasks.add_task(_process_cloud_message, incoming)

    log_event("message_received", channel="whatsapp_cloud", message_count=len(incoming_messages))
    return JSONResponse({"success": True, "queued": len(incoming_messages)})


async def _process_cloud_message(incoming) -> None:
    user_id = incoming.from_number
    started = None
    try:
        try:
            rate_limit = await check_rate_limit(user_id, scope="user", limit_type="message")
            if not rate_limit["allowed"]:
                log_event("abuse_detected", user_id=user_id, reason="rate_limit", retry_after=rate_limit["retry_after"])
                await send_text_message(user_id, "Too many messages right now. Please try again shortly.")
                return
        except RateLimitError as exc:
            log_error("Message rate limit check failed", user_id=user_id, error=str(exc))

        log_info(
            "Incoming WhatsApp Cloud message received",
            message_id=incoming.message_id,
            from_number=user_id,
            message_type=incoming.message_type,
        )

        conversation_state = await record_message_received(
            user_id=user_id,
            phone_number=user_id,
            message=incoming.body,
        )

        preferred_language = conversation_state.get("preferred_language") or detect_language(incoming.body)["language_code"]
        media_context = None
        if incoming.media_id:
            media_context = {
                "media_count": 1,
                "items": [
                    {
                        "media_id": incoming.media_id,
                        "media_type": incoming.message_type,
                        "content_type": incoming.media_mime_type,
                        "caption": incoming.media_caption,
                    }
                ],
            }

        ai_reply = conversation_state.get("language_switch_confirmation")
        agent_result = None
        if not ai_reply:
            agent_result = await run_agent(
                user_id=user_id,
                message=incoming.body,
                preferred_language=preferred_language,
                media_context=media_context,
            )
            ai_reply = agent_result["reply"]

        await send_text_message(user_id, ai_reply)
        await record_assistant_message(user_id, ai_reply)
        log_event(
            "whatsapp_reply_sent",
            message_id=incoming.message_id,
            from_number=user_id,
            preferred_language=preferred_language,
            agent_tool=(agent_result or {}).get("tool_result"),
        )
    except Exception as exc:
        log_error(
            "Cloud webhook background processing failed",
            from_number=user_id,
            message_id=incoming.message_id,
            error_type=type(exc).__name__,
            error=str(exc),
        )


async def _legacy_twilio_webhook(request: Request) -> Response:
    """
    Compatibility path for old Twilio form webhooks and existing tests.

    Production WhatsApp delivery now uses the Cloud API path above.
    """
    try:
        form = await request.form()
        form_data = dict(form)
        incoming = parse_twilio_form(form_data)
    except InvalidTwilioPayloadError as exc:
        log_error("Invalid Twilio webhook payload", error=str(exc))
        twiml = build_twiml_response("Sorry, I could not read that message. Please try again.")
        return Response(content=twiml, media_type="application/xml", status_code=400)

    log_info(
        "Incoming legacy Twilio message received",
        message_sid=incoming.message_sid,
        from_number=incoming.from_number,
        channel=incoming.channel,
        media_count=int(form_data.get("NumMedia") or 0),
    )

    uploaded_media = []
    media_context = None
    try:
        uploaded_media = await process_all_twilio_media(
            form_data,
            message_sid=incoming.message_sid,
            user_id=incoming.from_number,
        )
        media_context = await prepare_media_context(uploaded_media)
    except (WhatsAppMediaError, ValueError) as exc:
        log_error(
            "Legacy Twilio media processing failed",
            message_sid=incoming.message_sid,
            from_number=incoming.from_number,
            error=str(exc),
        )
        media_context = {"media_error": str(exc), "media_count": 0, "items": []}

    conversation_state = None
    try:
        conversation_state = await record_message_received(
            user_id=incoming.from_number,
            phone_number=incoming.from_number,
            message=incoming.body,
        )
    except Exception as exc:
        log_error(
            "Conversation lifecycle update failed",
            message_sid=incoming.message_sid,
            from_number=incoming.from_number,
            error_type=type(exc).__name__,
        )

    preferred_language = (conversation_state or {}).get("preferred_language") or detect_language(incoming.body)["language_code"]
    ai_reply = (conversation_state or {}).get("language_switch_confirmation")
    if not ai_reply:
        try:
            ai_reply = await generate_sales_reply(
                incoming.body,
                user_id=incoming.from_number,
                media_context=media_context,
                preferred_language=preferred_language,
            )
        except GroqServiceError as exc:
            log_error(
                "Groq AI response failed",
                message_sid=incoming.message_sid,
                from_number=incoming.from_number,
                preferred_language=preferred_language,
                error=str(exc),
            )
            ai_reply = "Sorry, I am having trouble responding right now. Please try again shortly."

    try:
        await record_assistant_message(incoming.from_number, ai_reply)
    except Exception as exc:
        log_error(
            "Assistant memory update failed",
            message_sid=incoming.message_sid,
            from_number=incoming.from_number,
            error_type=type(exc).__name__,
        )

    log_event(
        "legacy_twilio_reply_generated",
        message_sid=incoming.message_sid,
        from_number=incoming.from_number,
        channel=incoming.channel,
        media_count=len(uploaded_media),
        preferred_language=preferred_language,
    )

    twiml = build_twiml_response(ai_reply)
    return Response(content=twiml, media_type="application/xml")
