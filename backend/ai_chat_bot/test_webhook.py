import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import twilio_webhook
from app.routes.twilio_webhook import router
from app.services.groq_service import SYSTEM_PROMPT
from app.services.twilio_service import build_twiml_response
from app.utils.twilio_parser import InvalidTwilioPayloadError, parse_twilio_form


class TwilioWebhookTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_parse_twilio_form_extracts_required_fields(self):
        incoming = parse_twilio_form(
            {
                "Body": "Hello",
                "From": "whatsapp:+15550000000",
                "MessageSid": "SM123",
            }
        )

        self.assertEqual(incoming.body, "Hello")
        self.assertEqual(incoming.from_number, "whatsapp:+15550000000")
        self.assertEqual(incoming.message_sid, "SM123")
        self.assertEqual(incoming.channel, "whatsapp")

    def test_parse_twilio_form_rejects_missing_fields(self):
        with self.assertRaises(InvalidTwilioPayloadError):
            parse_twilio_form({"Body": "Hello"})

    def test_build_twiml_response_returns_valid_xml(self):
        twiml = build_twiml_response("Hello from AI")

        self.assertIn("<Response>", twiml)
        self.assertIn("<Message>Hello from AI</Message>", twiml)

    def test_sales_prompt_matches_business_assistant_behavior(self):
        self.assertIn("intelligent AI sales assistant", SYSTEM_PROMPT)
        self.assertIn("Ask one relevant question at a time", SYSTEM_PROMPT)
        self.assertIn("NEVER behave like ChatGPT", SYSTEM_PROMPT)

    def test_webhook_returns_ai_twiml_response(self):
        with (
            patch.object(twilio_webhook, "generate_sales_reply", new=AsyncMock(return_value="AI reply")),
            patch.object(twilio_webhook, "log_info"),
            patch.object(twilio_webhook, "log_event"),
        ):
            response = self.client.post(
                "/webhook",
                data={
                    "Body": "I need help with sales automation",
                    "From": "+15550000000",
                    "MessageSid": "SM123",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/xml")
        self.assertIn("<Message>AI reply</Message>", response.text)

    def test_webhook_handles_invalid_payload(self):
        with patch.object(twilio_webhook, "log_error"):
            response = self.client.post("/webhook", data={"Body": "Missing fields"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("<Message>Sorry, I could not read that message. Please try again.</Message>", response.text)

    def test_webhook_handles_groq_failure_with_fallback_twiml(self):
        with (
            patch.object(twilio_webhook, "generate_sales_reply", new=AsyncMock(side_effect=twilio_webhook.GroqServiceError("down"))),
            patch.object(twilio_webhook, "log_info"),
            patch.object(twilio_webhook, "log_error"),
            patch.object(twilio_webhook, "log_event"),
        ):
            response = self.client.post(
                "/webhook",
                data={
                    "Body": "Hello",
                    "From": "+15550000000",
                    "MessageSid": "SM123",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sorry, I am having trouble responding right now", response.text)


if __name__ == "__main__":
    unittest.main()
