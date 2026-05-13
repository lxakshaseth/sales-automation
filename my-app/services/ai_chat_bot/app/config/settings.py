import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

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
