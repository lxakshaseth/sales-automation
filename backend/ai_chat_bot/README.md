# FastAPI Twilio + Groq AI Chatbot Backend

Backend-only AI sales assistant for Twilio SMS/WhatsApp webhooks. Twilio sends an incoming message to `POST /webhook`, the backend calls Groq with the sales-assistant system prompt, and the response is returned as valid TwiML.

## Install

```bash
python -m pip install -r requirements.txt
```

## Environment

Create or update `.env`:

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
GROQ_API_KEY=your_groq_api_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
REDIS_URL=redis://localhost:6379/0
SMTP_EMAIL=your_gmail_or_smtp_sender@example.com
SMTP_PASSWORD=your_smtp_app_password
OWNER_EMAIL=owner1@example.com,owner2@example.com
REMINDER_AFTER_MINUTES=2
CLOSE_AFTER_MINUTES=5
```

## Run FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"status":"running"}
```

## Start ngrok

In another terminal:

```bash
ngrok http 8000
```

ngrok will show a public HTTPS URL, for example:

```text
https://xxxxx.ngrok-free.app
```

## Configure Twilio Webhook

In Twilio Console, configure your SMS or WhatsApp sender webhook:

```text
https://xxxxx.ngrok-free.app/webhook
```

Use:

```text
HTTP POST
```

## Webhook Flow

1. User sends SMS or WhatsApp message to Twilio.
2. Twilio sends `Body`, `From`, and `MessageSid` to `POST /webhook`.
3. Backend logs the incoming message.
4. Groq generates a reply using `llama-3.3-70b-versatile`.
5. Backend returns TwiML using `MessagingResponse`.
6. Twilio sends the AI reply back to the user.

## WhatsApp Media Flow

The webhook supports images, audio, video, PDFs, documents, and WhatsApp voice notes:

```text
WhatsApp Message
↓
Twilio Webhook
↓
Media Detection
↓
Download Media
↓
Cloudinary Upload
↓
AI Processing
↓
Store Metadata
↓
Agent Response
```

Twilio sends media fields such as:

```text
NumMedia=1
MediaUrl0=https://api.twilio.com/...
MediaContentType0=image/jpeg
```

The backend downloads the media temporarily, uploads it to Cloudinary with `resource_type="auto"`, returns the secure Cloudinary URL in metadata, and deletes the temp file.

Supported examples:

- Image: `MediaContentType0=image/jpeg`
- Audio or voice note: `MediaContentType0=audio/ogg`
- PDF: `MediaContentType0=application/pdf`
- Video: `MediaContentType0=video/mp4`

## Test Media Upload

After configuring Cloudinary credentials, send a WhatsApp Sandbox media message to your Twilio number. Watch the FastAPI logs for:

```text
Cloudinary upload success
WhatsApp media processed
twilio_reply_generated
```

## Future Architecture

The webhook is intentionally modular:

- `app/routes/` handles HTTP routing.
- `app/services/` handles Groq and Twilio response logic.
- `app/utils/` handles payload parsing.
- Existing modules support future Redis queue, memory, tool calling, scheduling, RAG, rate limiting, and event-driven workflows.

This keeps the webhook beginner-friendly while leaving room for multi-user autonomous AI agent systems.

## Autonomous Conversation Lifecycle

The backend now manages short-term sales conversations automatically:

```text
User Message
↓
Redis conversation state + JSON memory update
↓
APScheduler refreshes reminder and close jobs
↓
No reply after REMINDER_AFTER_MINUTES
↓
Outbound Twilio reminder
↓
Still inactive after CLOSE_AFTER_MINUTES
↓
Groq lead summary
↓
SMTP email to active owners
↓
Polite close message + Redis state marked closed
```

State is stored in Redis under `agent:conversation:{user_id}` with a 7-day TTL and an active-user set at `agent:conversation:active`. Conversation memory remains a JSON list under `agent:memory:{user_id}`.

Lifecycle fields tracked:

- `user_id`
- `phone_number`
- `last_message_time`
- `reminder_sent`
- `conversation_status`
- `conversation_start_time`
- `conversation_end_time`

Scheduler modules:

- `app/scheduler/reminder_scheduler.py` schedules and runs 2-minute inactivity reminders.
- `app/scheduler/close_chat_scheduler.py` schedules and runs 5-minute auto-close jobs.
- `app/scheduler/followup_scheduler.py` wraps future CRM and sales follow-up scheduling.

Services:

- `app/services/conversation_service.py` owns Redis lifecycle state and memory updates.
- `app/services/reminder_service.py` sends inactivity reminders through Twilio.
- `app/services/summary_service.py` generates Groq JSON lead summaries.
- `app/services/email_service.py` sends owner summary emails.
- `app/services/owner_settings_service.py` manages the `owner_settings` SQLite table.

## Owner Email Settings

Static owners can be configured with `OWNER_EMAIL` as a comma-separated list. Dynamic owners are stored in the local `owner_settings` table:

```text
id
email
active
created_at
```

Runtime endpoints:

```bash
curl http://localhost:8000/owner-settings/emails

curl -X POST http://localhost:8000/owner-settings/emails \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"owner@example.com\",\"active\":true}"

curl -X PATCH http://localhost:8000/owner-settings/emails \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"owner@example.com\",\"active\":false}"

curl -X DELETE "http://localhost:8000/owner-settings/emails?email=owner@example.com"
```

## Testing Reminders And Auto-Close

For quick local testing, reduce the timeout values:

```env
REMINDER_AFTER_MINUTES=0.1
CLOSE_AFTER_MINUTES=0.2
```

Run FastAPI, send a WhatsApp Sandbox message, then wait without replying. Watch logs for:

- `reminder_job_scheduled`
- `reminder_sent`
- `close_chat_job_scheduled`
- `summary_generated`
- `email_sent`
- `conversation_closed`

Run automated tests:

```bash
python -m unittest test_memory.py test_scheduler.py test_conversation_lifecycle.py
```
