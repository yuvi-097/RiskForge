"""
Alert API routes (admin-only).

Endpoints:
    GET   /alerts/              — list all unresolved alerts
    PATCH /alerts/{id}/resolve  — mark an alert as resolved
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.alert import AlertList
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=AlertList)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all unresolved alerts. Requires admin privileges."""
    service = AlertService(db)
    return await service.list_unresolved(skip=skip, limit=limit)


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific alert as resolved. Requires admin privileges."""
    service = AlertService(db)
    return await service.resolve_alert(alert_id)
