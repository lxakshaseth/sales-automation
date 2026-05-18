from dotenv import load_dotenv
import os

load_dotenv()


def _parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse common environment boolean values while keeping production-safe defaults."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip().lower()
LOAD_TEST_ENVIRONMENTS = {"test", "testing", "loadtest", "load-test", "locust", "ci"}
LOAD_TEST_MODE = _parse_bool(os.getenv("LOAD_TEST_MODE"), default=ENVIRONMENT in LOAD_TEST_ENVIRONMENTS)
MOCK_AI = _parse_bool(os.getenv("MOCK_AI"), default=LOAD_TEST_MODE)
MOCK_EMAILS = _parse_bool(os.getenv("MOCK_EMAILS"), default=LOAD_TEST_MODE)
AI_WEBHOOK_TIMEOUT_SECONDS = float(os.getenv("AI_WEBHOOK_TIMEOUT_SECONDS", "15"))
AI_WEBHOOK_MAX_CONCURRENCY = int(os.getenv("AI_WEBHOOK_MAX_CONCURRENCY", "5"))
AI_REQUEST_TIMEOUT_SECONDS = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "5"))
WEBHOOK_FAST_ACK = _parse_bool(os.getenv("WEBHOOK_FAST_ACK"), default=LOAD_TEST_MODE)
CACHE_DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))
REPORT_HISTORY_CACHE_TTL_SECONDS = int(os.getenv("REPORT_HISTORY_CACHE_TTL_SECONDS", "30"))
OWNER_EMAIL_CACHE_TTL_SECONDS = int(os.getenv("OWNER_EMAIL_CACHE_TTL_SECONDS", "30"))
AI_RESPONSE_CACHE_TTL_SECONDS = int(os.getenv("AI_RESPONSE_CACHE_TTL_SECONDS", "300"))
REDIS_OPERATION_TIMEOUT_SECONDS = float(os.getenv("REDIS_OPERATION_TIMEOUT_SECONDS", "0.75"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_TOOL_MODEL = os.getenv("GROQ_TOOL_MODEL", "llama-3.3-70b-versatile")
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY_SECONDS = float(os.getenv("RETRY_BASE_DELAY_SECONDS", "0.5"))
RETRY_MAX_DELAY_SECONDS = float(os.getenv("RETRY_MAX_DELAY_SECONDS", "30"))
RETRY_TIMEOUT_SECONDS = float(os.getenv("RETRY_TIMEOUT_SECONDS", "20"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
LOG_STRUCTURED = os.getenv("LOG_STRUCTURED", "true").lower() == "true"
RATE_LIMIT_MESSAGES_PER_MINUTE = int(os.getenv("RATE_LIMIT_MESSAGES_PER_MINUTE", "10"))
RATE_LIMIT_EMAILS_PER_MINUTE = int(os.getenv("RATE_LIMIT_EMAILS_PER_MINUTE", "5"))
RATE_LIMIT_API_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_API_REQUESTS_PER_MINUTE", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
# Rate limiting is enabled by default in production. In explicit test/load-test
# environments it is disabled unless ENABLE_RATE_LIMIT/RATE_LIMIT_ENABLED says otherwise.
_rate_limit_default = ENVIRONMENT not in LOAD_TEST_ENVIRONMENTS
_rate_limit_env_value = os.getenv("ENABLE_RATE_LIMIT", os.getenv("RATE_LIMIT_ENABLED"))
_disable_rate_limit = _parse_bool(os.getenv("DISABLE_RATE_LIMIT"), default=False)
ENABLE_RATE_LIMIT = _parse_bool(_rate_limit_env_value, default=_rate_limit_default)
if _disable_rate_limit:
    ENABLE_RATE_LIMIT = False
RATE_LIMIT_ENABLED = ENABLE_RATE_LIMIT
RATE_LIMIT_DISABLED_REASON = (
    "DISABLE_RATE_LIMIT=true"
    if _disable_rate_limit
    else
    "explicit environment override"
    if _rate_limit_env_value is not None and not ENABLE_RATE_LIMIT
    else f"ENVIRONMENT={ENVIRONMENT}"
    if not ENABLE_RATE_LIMIT
    else ""
)
RATE_LIMIT_BYPASS_LOCALHOST = os.getenv("RATE_LIMIT_BYPASS_LOCALHOST", "false").lower() in {"1", "true", "yes", "on"}
DEBUG_HTTP_LOGGING = os.getenv("DEBUG_HTTP_LOGGING", "false").lower() in {"1", "true", "yes", "on"}
DEBUG_HTTP_BODY_LOGGING = os.getenv("DEBUG_HTTP_BODY_LOGGING", "false").lower() in {"1", "true", "yes", "on"}
DEBUG_HTTP_BODY_MAX_CHARS = int(os.getenv("DEBUG_HTTP_BODY_MAX_CHARS", "2000"))

def _normalize_redis_url(value: str | None) -> str | None:
    """Accept a raw Redis URL and tolerate accidental `redis-cli -u` prefixes."""
    if not value:
        return None

    value = value.strip()
    cli_prefix = "redis-cli -u "
    if value.startswith(cli_prefix):
        return value.removeprefix(cli_prefix).strip()

    return value


REDIS_URL = _normalize_redis_url(os.getenv("REDIS_URL"))
REDIS_MEMORY_TTL_SECONDS = int(os.getenv("REDIS_MEMORY_TTL_SECONDS", str(7 * 24 * 60 * 60)))
REDIS_CONVERSATION_TTL_SECONDS = int(os.getenv("REDIS_CONVERSATION_TTL_SECONDS", str(7 * 24 * 60 * 60)))
REMINDER_AFTER_MINUTES = float(os.getenv("REMINDER_AFTER_MINUTES", "2"))
CLOSE_AFTER_MINUTES = float(os.getenv("CLOSE_AFTER_MINUTES", "5"))
CONVERSATION_DB_PATH = os.getenv("CONVERSATION_DB_PATH", "data/conversations.db")

EMAIL_HOST = os.getenv("EMAIL_HOST") or os.getenv("SMTP_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER") or os.getenv("SMTP_EMAIL")
EMAIL_PASS = os.getenv("EMAIL_PASS") or os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM") or EMAIL_USER
EMAIL_TIMEOUT_SECONDS = float(os.getenv("EMAIL_TIMEOUT_SECONDS", "20"))
EMAIL_RETRY_ATTEMPTS = int(os.getenv("EMAIL_RETRY_ATTEMPTS", "3"))
SMTP_HOST = EMAIL_HOST
SMTP_PORT = EMAIL_PORT
SMTP_EMAIL = EMAIL_USER
SMTP_PASSWORD = EMAIL_PASS
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_PHONE_NUMBER = TWILIO_WHATSAPP_NUMBER

WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "twilio").strip().lower()
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
META_APP_SECRET = os.getenv("META_APP_SECRET")
WHATSAPP_GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v19.0")
WHATSAPP_GRAPH_BASE_URL = os.getenv("WHATSAPP_GRAPH_BASE_URL", "https://graph.facebook.com")
WHATSAPP_WEBHOOK_SIGNATURE_REQUIRED = os.getenv("WHATSAPP_WEBHOOK_SIGNATURE_REQUIRED", "true").lower() == "true"
WHATSAPP_SEND_RETRY_ATTEMPTS = int(os.getenv("WHATSAPP_SEND_RETRY_ATTEMPTS", "3"))

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_ACCESS_TOKEN = os.getenv("GOOGLE_ACCESS_TOKEN")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
GOOGLE_CALENDAR_TIMEZONE = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "UTC")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_agent")
