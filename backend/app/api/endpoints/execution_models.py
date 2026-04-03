"""
Admin API: каталог execution_models (фаза 10 data plane).

Только чтение v0; изменение политик — миграции/сид или будущий super-admin.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.execution_model import ExecutionModel
from app.models.user import User

router = APIRouter()


class ExecutionModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    model_key: str
    display_name: str
    description: Optional[str]
    fill_rule: Optional[dict]
    slippage_policy: Optional[dict]
    fee_policy: Optional[dict]
    expiry_policy: Optional[dict]
    is_active: bool
    sort_order: int
    created_at: object
    updated_at: object


@router.get("/", response_model=List[ExecutionModelRead])
def list_execution_models(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    active_only: bool = Query(True, description="Только is_active=true"),
):
    q = db.query(ExecutionModel)
    if active_only:
        q = q.filter(ExecutionModel.is_active.is_(True))
    return q.order_by(ExecutionModel.sort_order.asc(), ExecutionModel.id.asc()).all()


@router.get("/by-key/{model_key}", response_model=ExecutionModelRead)
def get_execution_model_by_key(
    model_key: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = (
        db.query(ExecutionModel)
        .filter(ExecutionModel.model_key == model_key.strip().lower())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="execution model not found")
    return row


@router.get("/{execution_model_id}", response_model=ExecutionModelRead)
def get_execution_model(
    execution_model_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = db.query(ExecutionModel).filter(ExecutionModel.id == execution_model_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="execution model not found")
    return row
