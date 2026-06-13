import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from app.config.settings import settings
from app.core.logger import log_error, log_event, log_info
from app.core.rate_limiter import RateLimitError, check_rate_limit
from app.security import secure_process_request
from app.services.ai_media_processor import prepare_media_context
from app.services.conversation_service import record_assistant_message, record_message_received
from app.services.language_service import detect_language
from app.services.twilio_service import build_twiml_response
from app.services.whatsapp_cloud_service import (
    WhatsAppCloudError,
    parse_incoming_messages,
    read_json_body,
    verify_meta_signature,
    verify_webhook_token,
)
from app.services.whatsapp_media_service import WhatsAppMediaError, process_all_twilio_media
from app.services.whatsapp_provider import META_PROVIDER, get_active_provider, send_whatsapp_message
from app.utils.twilio_parser import InvalidTwilioPayloadError, parse_twilio_form

router = APIRouter()

AI_FALLBACK_REPLY = "Thanks for your message. Our team will follow up shortly."
_ai_webhook_semaphore = asyncio.Semaphore(max(1, settings.ai_webhook_max_concurrency))


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

    if get_active_provider() != META_PROVIDER:
        log_event("meta_webhook_ignored", active_provider=get_active_provider())
        return JSONResponse({"success": True, "queued": 0, "provider": get_active_provider()})

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


@router.post("/webhook/twilio/whatsapp")
async def twilio_whatsapp_webhook(request: Request) -> Response:
    """
    Receive Twilio WhatsApp form webhooks at the URL configured in Twilio.

    Twilio sends application/x-www-form-urlencoded payloads with fields such as
    Body, From, To, MessageSid, NumMedia, and MediaUrl0.
    """
    return await _handle_twilio_form_webhook(
        request,
        received_log_message="Incoming Twilio WhatsApp webhook received",
        reply_event_name="twilio_whatsapp_reply_generated",
    )


async def _process_cloud_message(incoming) -> None:
    user_id = incoming.from_number
    try:
        try:
            rate_limit = await check_rate_limit(user_id, scope="user", limit_type="message")
            if not rate_limit["allowed"]:
                log_event("abuse_detected", user_id=user_id, reason="rate_limit", retry_after=rate_limit["retry_after"])
                await send_whatsapp_message(user_id, "Too many messages right now. Please try again shortly.")
                return
        except RateLimitError as exc:
            log_error("Message rate limit check failed", user_id=user_id, error=str(exc))

        log_info(
            "Incoming WhatsApp Cloud message received",
            message_id=incoming.message_id,
            from_number=user_id,
            message_type=incoming.message_type,
        )

        try:
            conversation_state = await record_message_received(
                user_id=user_id,
                phone_number=user_id,
                message=incoming.body,
            )
        except Exception as exc:
            log_error("Conversation lifecycle update failed", from_number=user_id, error_type=type(exc).__name__)
            conversation_state = {}

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
            secured_response = await _generate_secured_reply_with_timeout(
                user_message=incoming.body,
                user_id=user_id,
                media_context=media_context,
                preferred_language=preferred_language,
                message_sid=incoming.message_id,
                channel="whatsapp_cloud",
            )
            ai_reply = secured_response["reply"]
            agent_result = secured_response["metadata"]

        await send_whatsapp_message(user_id, ai_reply)
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
    return await _handle_twilio_form_webhook(
        request,
        received_log_message="Incoming legacy Twilio message received",
        reply_event_name="legacy_twilio_reply_generated",
    )


async def _handle_twilio_form_webhook(
    request: Request,
    *,
    received_log_message: str,
    reply_event_name: str,
) -> Response:
    try:
        form = await request.form()
        form_data = dict(form)
        incoming = parse_twilio_form(form_data)
        media_count = _parse_twilio_media_count(form_data)
    except InvalidTwilioPayloadError as exc:
        log_error("Invalid Twilio webhook payload", error=str(exc))
        twiml = build_twiml_response("Sorry, I could not read that message. Please try again.")
        return Response(content=twiml, media_type="application/xml", status_code=400)
    except ValueError as exc:
        log_error("Invalid Twilio webhook payload", error=str(exc))
        twiml = build_twiml_response("Sorry, I could not read that message. Please try again.")
        return Response(content=twiml, media_type="application/xml", status_code=400)

    log_info(
        received_log_message,
        message_sid=incoming.message_sid,
        from_number=incoming.from_number,
        channel=incoming.channel,
        body_preview=incoming.body[:120],
        media_count=media_count,
        form_keys=sorted(form_data.keys()),
    )

    explicit_fast_ack = request.headers.get("x-fast-ack", "").lower() in {"1", "true", "yes", "on"}
    load_test_fast_ack = settings.webhook_fast_ack and bool(request.headers.get("x-load-test"))
    if explicit_fast_ack or load_test_fast_ack:
        log_event(
            "twilio_webhook_fast_ack",
            message_sid=incoming.message_sid,
            from_number=incoming.from_number,
            load_test_mode=settings.load_test_mode,
        )
        return Response(content=build_twiml_response(AI_FALLBACK_REPLY), media_type="application/xml")

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
        explicit_mock_ai = request.headers.get("x-mock-ai", "").lower() in {"1", "true", "yes", "on"}
        load_test_mock_ai = settings.mock_ai and bool(request.headers.get("x-load-test"))
        if explicit_mock_ai or load_test_mock_ai:
            ai_reply = AI_FALLBACK_REPLY
            log_event(
                "mock_ai_reply_used",
                message_sid=incoming.message_sid,
                from_number=incoming.from_number,
                load_test_mode=settings.load_test_mode,
            )
        else:
            if _ai_webhook_semaphore.locked():
                log_error(
                    "AI webhook concurrency saturated",
                    message_sid=incoming.message_sid,
                    from_number=incoming.from_number,
                    max_concurrency=settings.ai_webhook_max_concurrency,
                )
                ai_reply = AI_FALLBACK_REPLY
            else:
                secured_response = await _generate_secured_reply_with_timeout(
                    user_message=incoming.body,
                    user_id=incoming.from_number,
                    media_context=media_context,
                    preferred_language=preferred_language,
                    message_sid=incoming.message_sid,
                    channel=incoming.channel,
                )
                ai_reply = secured_response["reply"]

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
        reply_event_name,
        message_sid=incoming.message_sid,
        from_number=incoming.from_number,
        channel=incoming.channel,
        media_count=len(uploaded_media),
        preferred_language=preferred_language,
    )

    twiml = build_twiml_response(ai_reply)
    return Response(content=twiml, media_type="application/xml")


async def _generate_secured_reply_with_timeout(
    *,
    user_message: str,
    user_id: str,
    media_context: dict | None,
    preferred_language: str,
    message_sid: str,
    channel: str,
) -> dict:
    async with _ai_webhook_semaphore:
        try:
            # Keep webhook latency bounded. Twilio expects a quick response,
            # and load tests should not pile up behind slow model calls.
            response = await asyncio.wait_for(
                secure_process_request(
                    {
                        "user_query": user_message,
                        "user_id": user_id,
                        "tenant_id": "default",
                        "channel": channel,
                        "preferred_language": preferred_language,
                        "metadata": {"tenant_id": "default", "message_sid": message_sid, "media_context": media_context or {}},
                        "timeout_seconds": settings.ai_webhook_timeout_seconds,
                    }
                ),
                timeout=settings.ai_webhook_timeout_seconds,
            )
            return {
                "reply": response.response,
                "metadata": {
                    "success": response.success,
                    "action": response.action,
                    "security": response.metadata.get("security"),
                    "security_blocked": response.metadata.get("security_blocked", False),
                    "trace_steps": [trace.step for trace in response.traces],
                },
            }
        except TimeoutError:
            log_error(
                "Secured AI response timed out",
                message_sid=message_sid,
                from_number=user_id,
                preferred_language=preferred_language,
                timeout_seconds=settings.ai_webhook_timeout_seconds,
            )
            return {"reply": AI_FALLBACK_REPLY, "metadata": {"success": False, "action": "fallback_response", "error": "timeout"}}
        except Exception as exc:
            log_error(
                "Secured AI response failed",
                message_sid=message_sid,
                from_number=user_id,
                preferred_language=preferred_language,
                error=str(exc),
            )
            return {"reply": "Sorry, I am having trouble responding right now. Please try again shortly.", "metadata": {"success": False, "action": "fallback_response", "error": str(exc)}}


def _parse_twilio_media_count(form_data: dict) -> int:
    try:
        return int(form_data.get("NumMedia") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("NumMedia must be an integer") from exc
