import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip().lower()
LOAD_TEST_ENVIRONMENTS = {"test", "testing", "loadtest", "load-test", "locust", "ci"}
LOAD_TEST_MODE = _parse_bool(os.getenv("LOAD_TEST_MODE"), default=ENVIRONMENT in LOAD_TEST_ENVIRONMENTS)
_DISABLE_RATE_LIMIT = _parse_bool(os.getenv("DISABLE_RATE_LIMIT"), default=False)
_ENABLE_RATE_LIMIT = _parse_bool(
    os.getenv("ENABLE_RATE_LIMIT", os.getenv("RATE_LIMIT_ENABLED")),
    default=ENVIRONMENT not in LOAD_TEST_ENVIRONMENTS,
)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    environment: str = ENVIRONMENT
    load_test_mode: bool = LOAD_TEST_MODE
    mock_ai: bool = _parse_bool(os.getenv("MOCK_AI"), default=LOAD_TEST_MODE)
    mock_emails: bool = _parse_bool(os.getenv("MOCK_EMAILS"), default=LOAD_TEST_MODE)
    ai_webhook_timeout_seconds: float = float(os.getenv("AI_WEBHOOK_TIMEOUT_SECONDS", "2.5"))
    ai_webhook_max_concurrency: int = int(os.getenv("AI_WEBHOOK_MAX_CONCURRENCY", "5"))
    ai_request_timeout_seconds: float = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "5"))
    webhook_fast_ack: bool = _parse_bool(os.getenv("WEBHOOK_FAST_ACK"), default=LOAD_TEST_MODE)
    cache_default_ttl_seconds: int = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))
    report_history_cache_ttl_seconds: int = int(os.getenv("REPORT_HISTORY_CACHE_TTL_SECONDS", "30"))
    owner_email_cache_ttl_seconds: int = int(os.getenv("OWNER_EMAIL_CACHE_TTL_SECONDS", "30"))
    ai_response_cache_ttl_seconds: int = int(os.getenv("AI_RESPONSE_CACHE_TTL_SECONDS", "300"))
    redis_operation_timeout_seconds: float = float(os.getenv("REDIS_OPERATION_TIMEOUT_SECONDS", "0.5"))
    enable_rate_limit: bool = False if _DISABLE_RATE_LIMIT else _ENABLE_RATE_LIMIT
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    twilio_account_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number: str | None = os.getenv("TWILIO_WHATSAPP_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
    whatsapp_provider: str = os.getenv("WHATSAPP_PROVIDER", "twilio").strip().lower()
    whatsapp_access_token: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str | None = os.getenv("WHATSAPP_VERIFY_TOKEN")
    meta_app_secret: str | None = os.getenv("META_APP_SECRET")
    whatsapp_graph_api_version: str = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v19.0")
    redis_url: str | None = os.getenv("REDIS_URL")
    smtp_email: str | None = os.getenv("SMTP_EMAIL")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    owner_email: str = os.getenv("OWNER_EMAIL", "")
    reminder_after_minutes: float = float(os.getenv("REMINDER_AFTER_MINUTES", "2"))
    close_after_minutes: float = float(os.getenv("CLOSE_AFTER_MINUTES", "5"))
    cloudinary_cloud_name: str | None = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str | None = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret: str | None = os.getenv("CLOUDINARY_API_SECRET")

    @property
    def missing_twilio_values(self) -> list[str]:
        missing = []
        if not self.twilio_account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.twilio_whatsapp_number:
            missing.append("TWILIO_WHATSAPP_NUMBER")
        return missing

    @property
    def missing_whatsapp_cloud_values(self) -> list[str]:
        missing = []
        if not self.whatsapp_access_token:
            missing.append("WHATSAPP_ACCESS_TOKEN")
        if not self.whatsapp_phone_number_id:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if not self.whatsapp_verify_token:
            missing.append("WHATSAPP_VERIFY_TOKEN")
        return missing

    @property
    def missing_groq_values(self) -> list[str]:
        return [] if self.groq_api_key else ["GROQ_API_KEY"]

    @property
    def missing_cloudinary_values(self) -> list[str]:
        missing = []
        if not self.cloudinary_cloud_name:
            missing.append("CLOUDINARY_CLOUD_NAME")
        if not self.cloudinary_api_key:
            missing.append("CLOUDINARY_API_KEY")
        if not self.cloudinary_api_secret:
            missing.append("CLOUDINARY_API_SECRET")
        return missing


settings = Settings()
