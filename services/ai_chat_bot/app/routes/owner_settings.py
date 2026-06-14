from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.owner_settings_service import (
    OwnerSettingsError,
    add_owner_email,
    list_owner_emails,
    remove_owner_email,
    update_owner_email,
)

router = APIRouter(prefix="/owner-settings", tags=["owner-settings"])


class OwnerEmailRequest(BaseModel):
    email: str
    active: bool = True


@router.get("/emails")
async def get_owner_emails(active_only: bool = False):
    return {"emails": await list_owner_emails(active_only=active_only)}


@router.post("/emails")
async def create_owner_email(payload: OwnerEmailRequest):
    try:
        return await add_owner_email(payload.email, active=payload.active)
    except (OwnerSettingsError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/emails")
async def patch_owner_email(payload: OwnerEmailRequest):
    try:
        return await update_owner_email(payload.email, active=payload.active)
    except (OwnerSettingsError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/emails")
async def delete_owner_email(email: str):
    try:
        return {"removed": await remove_owner_email(email)}
    except (OwnerSettingsError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
