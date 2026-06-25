from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from app.core.agent_executor import close_agent_executor_client
from app.core.debugging import DebugRequestMiddleware, install_exception_handlers
from app.core.event_bus import close_event_bus
from app.core.llm import close_llm_client
from app.core.logger import LoggingMiddleware, configure_logging
from app.core.performance import PerformanceMiddleware
from app.core.rate_limiter import close_rate_limiter, install_rate_limit_middleware
from app.core.redis_utils import validate_redis_startup
from app.routes.owner_settings import router as owner_settings_router
from app.routes.reports import router as reports_router
from app.routes.leads_analytics import router as leads_analytics_router
from app.routes.twilio_webhook import router as twilio_router
from app.scheduler.followup import shutdown_scheduler, start_scheduler
from app.security import secure_process_request
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
    await validate_redis_startup()
    print_registered_routes(app)
    await init_owner_settings_db()
    await start_scheduler()
    yield
    await shutdown_scheduler()
    await close_llm_client()
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
install_exception_handlers(app)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(DebugRequestMiddleware)
app.add_middleware(LoggingMiddleware)
install_rate_limit_middleware(app)
app.include_router(twilio_router)
app.include_router(owner_settings_router)
app.include_router(reports_router)
app.include_router(leads_analytics_router)

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/ask")
async def ask(q: str, tenant_id: str = "default", user_id: str | None = None):
    response = await secure_process_request(
        {
            "user_query": q,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "channel": "default",
            "metadata": {"tenant_id": tenant_id, "entrypoint": "/ask"},
            "timeout_seconds": 5.0,
        }
    )
    return {"response": response.response, "success": response.success, "action": response.action, "security": response.metadata.get("security")}


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
