import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services import whatsapp_provider


class WhatsAppProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_twilio_is_default_active_provider(self):
        with patch.object(whatsapp_provider, "settings", SimpleNamespace(whatsapp_provider="twilio")):
            self.assertEqual(whatsapp_provider.get_active_provider(), "twilio")

    async def test_unknown_provider_falls_back_to_twilio(self):
        with patch.object(whatsapp_provider, "settings", SimpleNamespace(whatsapp_provider="cloud")):
            self.assertEqual(whatsapp_provider.get_active_provider(), "twilio")

    async def test_text_message_uses_twilio_when_provider_is_twilio(self):
        with (
            patch.object(whatsapp_provider, "settings", SimpleNamespace(whatsapp_provider="twilio")),
            patch.object(
                whatsapp_provider.twilio_service,
                "send_whatsapp_message",
                new=AsyncMock(return_value={"sid": "SM123", "status": "queued", "to": "whatsapp:+15550000000"}),
            ) as twilio_send,
            patch.object(whatsapp_provider.whatsapp_cloud_service, "send_text_message", new=AsyncMock()) as meta_send,
        ):
            result = await whatsapp_provider.send_whatsapp_message("whatsapp:+15550000000", "Hello")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "twilio")
        twilio_send.assert_awaited_once_with("whatsapp:+15550000000", "Hello", media_url=None)
        meta_send.assert_not_awaited()

    async def test_media_message_uses_twilio_media_url_when_provider_is_twilio(self):
        with (
            patch.object(whatsapp_provider, "settings", SimpleNamespace(whatsapp_provider="twilio")),
            patch.object(
                whatsapp_provider.twilio_service,
                "send_whatsapp_message",
                new=AsyncMock(return_value={"sid": "SM124", "status": "queued", "to": "whatsapp:+15550000000"}),
            ) as twilio_send,
        ):
            result = await whatsapp_provider.send_whatsapp_media(
                "whatsapp:+15550000000",
                "https://example.com/brochure.pdf",
                caption="Here is the brochure.",
            )

        self.assertTrue(result["success"])
        twilio_send.assert_awaited_once_with(
            "whatsapp:+15550000000",
            "Here is the brochure.",
            media_url="https://example.com/brochure.pdf",
        )


if __name__ == "__main__":
    unittest.main()
