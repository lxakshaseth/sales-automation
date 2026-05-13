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

## Docker Setup

The backend can run with Docker Compose from the `backend/ai_chat_bot` folder.

Expected folder structure:

```text
backend/
└── ai_chat_bot/
    ├── app/
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── .dockerignore
    └── .env
```

Start all containers:

```bash
cd backend/ai_chat_bot
docker compose up --build
```

Stop and remove the containers:

```bash
docker compose down
```

The Compose stack starts:

- `ai_chat_bot_app`: FastAPI on `http://localhost:8000`
- `ai_chat_bot_redis`: Redis on port `6379`
- `ai_chat_bot_celery_worker`: Celery worker
- `ai_chat_bot_celery_beat`: Celery beat scheduler

FastAPI uses hot reload in Compose by mounting `./app:/app/app` and running:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Celery services use the requested commands:

```bash
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

Compose loads secrets and API keys from `.env` using `env_file`. Inside Docker,
Redis is reached through the service hostname:

```env
REDIS_URL=redis://redis:6379/0
WHATSAPP_PROVIDER=twilio
```

### Docker Verification

After `docker compose up --build` finishes, verify:

```bash
docker compose ps
```

Expected:

- `ai_chat_bot_app` is running and healthy.
- `ai_chat_bot_redis` is running and healthy.
- `ai_chat_bot_celery_worker` is running.
- `ai_chat_bot_celery_beat` is running.

Open FastAPI docs:

```text
http://localhost:8000/docs
```

Check the API health endpoint:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"status":"running"}
```

Check Redis:

```bash
docker compose exec redis redis-cli ping
```

Expected response:

```text
PONG
```

Check Celery logs:

```bash
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

Expected:

- Worker starts without import errors.
- Worker connects to `redis://redis:6379/1`.
- Beat starts and keeps running.

### Docker Troubleshooting

Missing `docker-compose.yml`:

```bash
cd backend/ai_chat_bot
dir
```

Make sure `docker-compose.yml` is in the same folder as `Dockerfile` and
`requirements.txt`, then run:

```bash
docker compose up --build
```

Redis connection issues:

- Use `redis://redis:6379/0` inside Docker, not `redis://localhost:6379/0`.
- Confirm Redis is healthy:

```bash
docker compose ps redis
docker compose exec redis redis-cli ping
```

Celery import issues:

- Confirm the module exists:

```bash
docker compose exec app python -c "from app.workers.celery_app import celery_app; print(celery_app.main)"
```

- Rebuild after dependency changes:

```bash
docker compose build --no-cache
docker compose up
```

Port conflicts:

- If port `8000` is already in use, change the app port mapping in
  `docker-compose.yml` from `"8000:8000"` to `"8001:8000"` and open
  `http://localhost:8001/docs`.
- If port `6379` is already in use, change Redis from `"6379:6379"` to
  `"6380:6379"`. Other containers can still use `redis://redis:6379/0`.

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

## AI Sales Reports

The backend generates enterprise-style sales conversation reports after chat
completion. The auto-close scheduler queues a Celery report task after a
conversation is closed. If Celery is unavailable, it falls back to inline async
generation so the report flow does not crash the scheduler.

Report pipeline:

```text
WhatsApp/User Chat
↓
Conversation Stored In Redis
↓
Groq AI Summary + Lead Analysis
↓
Responsive HTML Report Rendered
↓
Email Sent To Sales/Admin Team
↓
Report Stored For Future CRM Sync
```

### Gmail SMTP Configuration

Use Gmail SMTP with an app password, not your normal Gmail password:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-gmail-address@gmail.com
EMAIL_PASS=your 16 digit app password
EMAIL_FROM=your-gmail-address@gmail.com
OWNER_EMAIL=sales@example.com,admin@example.com
```

The backend automatically removes spaces from `EMAIL_PASS`, so both
`abcd efgh ijkl mnop` and `abcdefghijklmnop` work.

Verify SMTP from the running API:

```bash
curl http://localhost:8000/test-email
```

Send to a specific recipient:

```bash
curl "http://localhost:8000/test-email?to=sales@example.com"
```

Successful response:

```json
{
  "success": true,
  "message": "Test email sent successfully",
  "recipients": ["sales@example.com"]
}
```

Expected report-email logs:

```text
Generating AI summary...
Preparing HTML email...
Connecting to Gmail SMTP...
Starting SMTP TLS...
Authenticating Gmail SMTP...
Sending summary email...
Summary email sent successfully
```

Gmail troubleshooting:

- Enable 2-Step Verification on the Gmail account.
- Generate a Gmail App Password and put it in `EMAIL_PASS`.
- Do not use your normal Gmail login password.
- Keep `EMAIL_HOST=smtp.gmail.com` and `EMAIL_PORT=587`.
- Confirm `EMAIL_USER` and `EMAIL_FROM` are valid email addresses.
- If Docker is used, rebuild/restart after changing `.env`:

```bash
docker compose down
docker compose up --build
```

- If auth fails, logs will mention Gmail SMTP authentication failure.
- If Docker networking blocks SMTP, logs will mention timeout or connection refused.
- If no report recipients exist, set `OWNER_EMAIL` or add owners through `/owner-settings/emails`.

Generate a report manually:

```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"whatsapp:+15550000000\",\"company_name\":\"INDUX TECHNOLOGY\",\"conversation_source\":\"WhatsApp\",\"send_email\":true}"
```

Queue report generation through Celery:

```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"whatsapp:+15550000000\",\"send_email\":true,\"async_processing\":true}"
```

Example queued response:

```json
{
  "queued": true,
  "task_id": "3f3b7d8e-1a5f-4b2d-9b7d-23f8f4b935a0",
  "report": null
}
```

Read a report:

```bash
curl http://localhost:8000/reports/rep_example123
```

Send an existing report email:

```bash
curl -X POST http://localhost:8000/reports/send-email \
  -H "Content-Type: application/json" \
  -d "{\"report_id\":\"rep_example123\"}"
```

View report history:

```bash
curl http://localhost:8000/reports/history
```

Example generated report fields:

```json
{
  "company_name": "INDUX TECHNOLOGY",
  "client_name": "Rahul Sharma",
  "client_phone_number": "+91XXXXXXXXXX",
  "client_email": "rahul@example.com",
  "conversation_source": "WhatsApp",
  "language": "Hindi / Hinglish",
  "topic_of_discussion": [
    "Client asked about pricing",
    "Interested in AI automation system",
    "Asked for WhatsApp integration"
  ],
  "client_requirements": [
    "WhatsApp chatbot",
    "CRM integration",
    "AI automation",
    "Email workflow"
  ],
  "lead_analysis": {
    "lead_type": "HOT LEAD",
    "interest_level": "High",
    "buying_intent": "Strong",
    "estimated_closing_probability": 85
  },
  "ai_remarks": "Client showed urgent buying intent and asked implementation-related questions.",
  "next_actions": [
    "Send pricing PDF",
    "Schedule demo meeting",
    "Create CRM lead"
  ]
}
```

Report files:

- `app/models/summary_models.py` and `app/models/report_models.py` define Pydantic contracts.
- `app/services/ai_summary_service.py` calls Groq and safely parses AI JSON.
- `app/services/transcript_service.py` normalizes multilingual Unicode transcripts.
- `app/services/report_service.py` renders HTML, stores reports, and sends email.
- `app/templates/sales_summary_template.html` contains the responsive email template.
- `app/tasks/summary_tasks.py` provides Celery tasks for summary generation, email sending, transcript formatting, and lead analysis.
- `app/routes/reports.py` exposes the report API.

Future CRM integration steps:

- Replace Redis report persistence with a CRM/report table.
- Map `lead_analysis.lead_type`, `client_requirements`, and `next_actions` to CRM fields.
- Add idempotency keys so one closed conversation creates one CRM lead.
- Sync report IDs back onto HubSpot or the selected CRM object.

Future PDF export support:

- Add a `/reports/{report_id}/pdf` route.
- Render the same sanitized HTML template to PDF with Playwright or WeasyPrint.
- Store the PDF URL on the report and attach it to owner emails.

Future analytics dashboard recommendations:

- Track hot lead count, average closing probability, common requirements, response times, and source quality.
- Add date filters and language filters.
- Visualize report history from the future CRM/report table.
