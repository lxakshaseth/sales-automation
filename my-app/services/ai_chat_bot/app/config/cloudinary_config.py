import cloudinary
from dotenv import load_dotenv

from app.config.settings import settings

load_dotenv()


class CloudinaryConfigError(RuntimeError):
    """Raised when Cloudinary credentials are missing."""


def configure_cloudinary() -> None:
    """
    Configure Cloudinary's Python SDK.

    The backend SDK signs uploads using cloud_name, api_key, and api_secret, so
    browser-side unsigned upload presets are not needed for this Twilio workflow.
    """
    missing = settings.missing_cloudinary_values
    if missing:
        raise CloudinaryConfigError(f"Missing Cloudinary environment variable(s): {', '.join(missing)}")

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
