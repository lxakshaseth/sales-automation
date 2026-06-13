import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import twilio_webhook
from app.routes.twilio_webhook import router
from app.services import media_service
from app.services.media_service import upload_any_file
from app.services.whatsapp_media_service import process_all_twilio_media, process_twilio_media
from app.utils.file_utils import (
    FileValidationError,
    cleanup_temp_file,
    detect_media_type,
    generate_unique_filename,
    validate_file_size,
    validate_mime_type,
)


class FileUtilsTests(unittest.TestCase):
    def test_detect_media_types(self):
        self.assertEqual(detect_media_type("image/jpeg"), "image")
        self.assertEqual(detect_media_type("audio/ogg"), "audio")
        self.assertEqual(detect_media_type("video/mp4"), "video")
        self.assertEqual(detect_media_type("application/pdf"), "document")
        self.assertEqual(detect_media_type("application/x-unknown"), "unsupported")

    def test_validate_mime_type_rejects_unsupported(self):
        with self.assertRaises(FileValidationError):
            validate_mime_type("application/x-unknown")

    def test_generate_unique_filename_uses_extension(self):
        filename = generate_unique_filename("application/pdf", "test")

        self.assertTrue(filename.startswith("test_"))
        self.assertTrue(filename.endswith(".pdf"))

    def test_validate_file_size_and_cleanup(self):
        handle = tempfile.NamedTemporaryFile(delete=False)
        try:
            handle.write(b"hello")
            handle.close()
            self.assertEqual(validate_file_size(handle.name), 5)
            cleanup_temp_file(handle.name)
            self.assertFalse(os.path.exists(handle.name))
        finally:
            cleanup_temp_file(handle.name)


class MediaServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_any_file_returns_normalized_response(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        try:
            handle.write(b"image")
            handle.close()
            with (
                patch.object(media_service, "configure_cloudinary"),
                patch.object(
                    media_service.cloudinary.uploader,
                    "upload",
                    return_value={
                        "secure_url": "https://res.cloudinary.com/demo/image/upload/file.jpg",
                        "public_id": "twilio/file",
                        "resource_type": "image",
                        "format": "jpg",
                        "bytes": 5,
                        "original_filename": "file",
                    },
                ),
            ):
                result = await upload_any_file(handle.name, content_type="image/jpeg", user_id="user-123")

            self.assertEqual(result["secure_url"], "https://res.cloudinary.com/demo/image/upload/file.jpg")
            self.assertEqual(result["public_id"], "twilio/file")
            self.assertEqual(result["media_type"], "image")
        finally:
            cleanup_temp_file(handle.name)


class WhatsAppMediaServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_twilio_media_cleans_temp_file(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_path = handle.name
        handle.write(b"pdf")
        handle.close()

        with (
            patch("app.services.whatsapp_media_service.download_twilio_media", new=AsyncMock(return_value=temp_path)),
            patch("app.services.whatsapp_media_service.upload_any_file", new=AsyncMock(return_value={"secure_url": "https://cloudinary.test/file.pdf", "public_id": "file", "resource_type": "raw", "format": "pdf", "media_type": "document"})),
        ):
            result = await process_twilio_media(
                media_url="https://api.twilio.com/media",
                content_type="application/pdf",
                message_sid="SM123",
                user_id="user-123",
            )

        self.assertEqual(result["secure_url"], "https://cloudinary.test/file.pdf")
        self.assertFalse(os.path.exists(temp_path))

    async def test_process_all_twilio_media_handles_multiple_files(self):
        with patch("app.services.whatsapp_media_service.process_twilio_media", new=AsyncMock(return_value={"secure_url": "https://cloudinary.test/file"})) as process:
            result = await process_all_twilio_media(
                {
                    "NumMedia": "2",
                    "MediaUrl0": "https://api.twilio.com/one",
                    "MediaContentType0": "image/jpeg",
                    "MediaUrl1": "https://api.twilio.com/two",
                    "MediaContentType1": "audio/ogg",
                },
                message_sid="SM123",
                user_id="user-123",
            )

        self.assertEqual(len(result), 2)
        self.assertEqual(process.await_count, 2)


class WebhookMediaTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_webhook_processes_media_before_groq_reply(self):
        with (
            patch.object(twilio_webhook, "process_all_twilio_media", new=AsyncMock(return_value=[{"secure_url": "https://cloudinary.test/image.jpg", "media_type": "image"}])) as process_media,
            patch.object(twilio_webhook, "prepare_media_context", new=AsyncMock(return_value={"media_count": 1, "items": [{"secure_url": "https://cloudinary.test/image.jpg"}]})) as media_context,
            patch.object(twilio_webhook, "generate_sales_reply", new=AsyncMock(return_value="Thanks, I received the image.")) as groq,
            patch.object(twilio_webhook, "log_info"),
            patch.object(twilio_webhook, "log_event"),
        ):
            response = self.client.post(
                "/webhook",
                data={
                    "Body": "Here is my requirement",
                    "From": "whatsapp:+15550000000",
                    "MessageSid": "SM123",
                    "NumMedia": "1",
                    "MediaUrl0": "https://api.twilio.com/media",
                    "MediaContentType0": "image/jpeg",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Thanks, I received the image.", response.text)
        process_media.assert_awaited_once()
        media_context.assert_awaited_once()
        self.assertEqual(groq.await_args.kwargs["media_context"]["media_count"], 1)


if __name__ == "__main__":
    unittest.main()
