import json
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import logger as app_logger
from app.core.logger import (
    LoggingMiddleware,
    configure_logging,
    get_request_id,
    log_action,
    log_error,
    log_event,
    log_info,
    reset_request_id,
    set_request_id,
)


class LoggerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = str(Path(self.temp_dir.name) / "app.log")
        app_logger._configured = False

    def tearDown(self):
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        app_logger._configured = False
        self.temp_dir.cleanup()

    def _configure_temp_logging(self):
        with (
            patch.object(app_logger, "LOG_FILE_PATH", self.log_file),
            patch.object(app_logger, "LOG_STRUCTURED", True),
            patch.object(app_logger, "LOG_MAX_BYTES", 1024 * 1024),
            patch.object(app_logger, "LOG_BACKUP_COUNT", 1),
        ):
            logger = configure_logging()

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, "baseFilename"):
                root_logger.removeHandler(handler)
                handler.close()

        return logger

    def _read_logs(self):
        return [json.loads(line) for line in Path(self.log_file).read_text(encoding="utf-8").splitlines()]

    def test_log_info_writes_structured_log(self):
        self._configure_temp_logging()
        token = set_request_id("req-123")

        log_info("Email sent", provider="resend")
        reset_request_id(token)

        logs = self._read_logs()
        self.assertEqual(logs[0]["message"], "Email sent")
        self.assertEqual(logs[0]["request_id"], "req-123")
        self.assertEqual(logs[0]["provider"], "resend")

    def test_log_error_writes_error_event(self):
        self._configure_temp_logging()

        log_error("WhatsApp timeout", provider="whatsapp")

        logs = self._read_logs()
        self.assertEqual(logs[0]["event_type"], "error")
        self.assertEqual(logs[0]["message"], "WhatsApp timeout")

    def test_log_action_and_event(self):
        self._configure_temp_logging()

        log_action("create_lead", user_id="user-123")
        log_event("appointment_booked", user_id="user-123")

        logs = self._read_logs()
        self.assertEqual(logs[0]["event_type"], "action")
        self.assertEqual(logs[0]["action"], "create_lead")
        self.assertEqual(logs[1]["event_type"], "event")
        self.assertEqual(logs[1]["event"], "appointment_booked")

    def test_request_id_context(self):
        token = set_request_id("req-abc")

        self.assertEqual(get_request_id(), "req-abc")
        reset_request_id(token)
        self.assertIsNone(get_request_id())

    def test_logging_middleware_adds_request_id_header(self):
        self._configure_temp_logging()
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/ping")
        async def ping():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/ping", headers={"x-request-id": "req-middleware"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-request-id"], "req-middleware")
        logs = self._read_logs()
        self.assertEqual(logs[0]["request_id"], "req-middleware")
        self.assertEqual(logs[0]["event"], "http_request")


if __name__ == "__main__":
    unittest.main()
