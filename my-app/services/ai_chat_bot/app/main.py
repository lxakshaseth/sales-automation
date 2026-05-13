from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.agent_executor import close_agent_executor_client
from app.core.event_bus import close_event_bus
from app.core.logger import LoggingMiddleware, configure_logging
from app.core.llm import ask_llm
from app.core.rate_limiter import RateLimitMiddleware, close_rate_limiter
from app.routes.owner_settings import router as owner_settings_router
from app.routes.reports import router as reports_router
from app.routes.twilio_webhook import router as twilio_router
from app.scheduler.followup import shutdown_scheduler, start_scheduler
from app.services.conversation_service import close_conversation_client
from app.services.email_service import EmailServiceError, log_email_startup_validation, send_test_email, validate_email_settings
from app.services.groq_service import close_groq_service_client
from app.services.memory_service import close_memory_service_client
from app.services.owner_settings_service import init_owner_settings_db
from app.services.report_service import close_report_service_client
from app.services.whatsapp_cloud_service import close_whatsapp_cloud_client
from app.tools.calendar_tool import close_calendar_client
from app.tools.crm_tool import close_hubspot_client
from app.tools.memory_tool import close_memory_client
from app.tools.mongo_tool import close_mongo_client


def print_registered_routes(app: FastAPI) -> None:
    """Print registered HTTP routes on startup to catch prefix/import issues."""
    print("Registered FastAPI routes:")
    for route in app.routes:
        methods = sorted(getattr(route, "methods", []) or [])
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)
        if path and methods:
            print(f"{','.join(methods):12s} {path} -> {name}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log_email_startup_validation()
    print_registered_routes(app)
    await init_owner_settings_db()
    await start_scheduler()
    yield
    await shutdown_scheduler()
    await close_agent_executor_client()
    await close_groq_service_client()
    await close_whatsapp_cloud_client()
    await close_memory_service_client()
    await close_report_service_client()
    await close_calendar_client()
    await close_hubspot_client()
    await close_event_bus()
    await close_rate_limiter()
    await close_memory_client()
    await close_conversation_client()
    await close_mongo_client()


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.include_router(twilio_router)
app.include_router(owner_settings_router)
app.include_router(reports_router)

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/ask")
async def ask(q: str):

    response = await ask_llm(q)

    return {
        "response": response
    }


@app.get("/test-email")
async def test_email(to: str | None = None):
    """Send a real Gmail SMTP test email and return detailed delivery status."""
    status = validate_email_settings()
    if not status["valid"]:
        return {"success": False, "message": "SMTP configuration is incomplete", "smtp": status}
    try:
        result = await send_test_email(to)
        return result | {"smtp": status}
    except EmailServiceError as exc:
        return {"success": False, "message": str(exc), "smtp": status}
