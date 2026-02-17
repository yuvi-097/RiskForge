"""
Alert service — list and resolve alerts (admin operations).
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertList, AlertResponse

logger = get_logger("alert_service")


class AlertService:
    """Orchestrates alert retrieval and resolution workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = AlertRepository(db)

    async def list_unresolved(
        self, *, skip: int = 0, limit: int = 50
    ) -> AlertList:
        """Return paginated unresolved alerts."""
        items, total = await self._repo.list_unresolved(skip=skip, limit=limit)
        return AlertList(
            total=total,
            items=[AlertResponse.model_validate(a) for a in items],
        )

    async def resolve_alert(self, alert_id: UUID) -> dict:
        """Mark an alert as resolved.

        Raises:
            HTTPException 404 if alert not found.
        """
        success = await self._repo.resolve(alert_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )
        logger.info("alert_resolved", alert_id=str(alert_id))
        return {"detail": "Alert resolved"}
