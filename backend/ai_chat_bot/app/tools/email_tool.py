import resend
from app.core.config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY

async def send_email(to, subject, body):

    params = {
        "from": "onboarding@resend.dev",
        "to": [to],
        "subject": subject,
        "html": body
    }

    email = resend.Emails.send(params)

    return email