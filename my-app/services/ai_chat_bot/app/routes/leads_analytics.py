from fastapi import APIRouter, Query
from app.services.lead_analytics_service import get_lead_funnel_by_status

router = APIRouter(prefix="/leads", tags=["leads-analytics"])

@router.get("/funnel/by-status")
async def lead_funnel_by_status(
    days: int = Query(default=7, ge=1, le=365)
):
    return await get_lead_funnel_by_status(days)