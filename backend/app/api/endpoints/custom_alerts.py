"""Pro: CRUD для пользовательских алертов."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.services.custom_alerts_service import custom_alerts_service

router = APIRouter()


class CustomAlertCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    webhook_url: Optional[str] = None


class CustomAlertUpdateBody(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    notification_methods: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    symbol: Optional[str] = None


@router.get("/custom/templates")
async def get_alert_templates():
    """Шаблоны алертов (без авторизации — только справочник)."""
    return custom_alerts_service.get_alert_templates()


@router.get("/custom", response_model=List[Dict[str, Any]])
async def list_custom_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return await custom_alerts_service.get_user_alerts(current_user, db)


@router.post("/custom", status_code=status.HTTP_201_CREATED)
async def create_custom_alert(
    body: CustomAlertCreateBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cfg = body.model_dump()
    return await custom_alerts_service.create_custom_alert(current_user, db, cfg)


@router.patch("/custom/{alert_id}")
async def patch_custom_alert(
    alert_id: str,
    body: CustomAlertUpdateBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    return await custom_alerts_service.update_alert(current_user, db, alert_id, data)


@router.delete("/custom/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_custom_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    await custom_alerts_service.delete_alert(current_user, db, alert_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
