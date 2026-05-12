from dotenv import load_dotenv
import os

load_dotenv()

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

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_PHONE_NUMBER = TWILIO_WHATSAPP_NUMBER

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
