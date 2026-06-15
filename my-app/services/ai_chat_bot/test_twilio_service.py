import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services import twilio_service
from app.services.twilio_service import TwilioServiceError, send_whatsapp_message


class _FakeResponse:
    status_code = 201
    text = '{"sid":"SM123","status":"queued"}'

    def raise_for_status(self):
        return None

    def json(self):
        return {"sid": "SM123", "status": "queued"}


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.post = AsyncMock(return_value=_FakeResponse())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class TwilioServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_whatsapp_message_does_not_double_prefix_to_number(self):
        fake_settings = SimpleNamespace(
            missing_twilio_values=[],
            twilio_account_sid="AC123",
            twilio_auth_token="token",
            twilio_whatsapp_number="whatsapp:+14155238886",
        )

        with (
            patch.object(twilio_service, "settings", fake_settings),
            patch.object(twilio_service.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            result = await send_whatsapp_message("whatsapp:+917256014047", "Hello")

        self.assertEqual(result["to"], "whatsapp:+917256014047")

    async def test_send_whatsapp_message_prefixes_raw_e164_number(self):
        fake_settings = SimpleNamespace(
            missing_twilio_values=[],
            twilio_account_sid="AC123",
            twilio_auth_token="token",
            twilio_whatsapp_number="whatsapp:+14155238886",
        )

        with (
            patch.object(twilio_service, "settings", fake_settings),
            patch.object(twilio_service.httpx, "AsyncClient", _FakeAsyncClient),
        ):
            result = await send_whatsapp_message("+917256014047", "Hello")

        self.assertEqual(result["to"], "whatsapp:+917256014047")

    async def test_send_whatsapp_message_rejects_empty_message(self):
        fake_settings = SimpleNamespace(
            missing_twilio_values=[],
            twilio_account_sid="AC123",
            twilio_auth_token="token",
            twilio_whatsapp_number="whatsapp:+14155238886",
        )

        with patch.object(twilio_service, "settings", fake_settings), self.assertRaises(TwilioServiceError):
            await send_whatsapp_message("whatsapp:+917256014047", "")


if __name__ == "__main__":
    unittest.main()
