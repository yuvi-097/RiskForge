"""
Alert repository — async data-access layer for the alerts table.
"""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


class AlertRepository:
    """Encapsulates all database operations for Alert entities."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        transaction_id: UUID,
        alert_type: str,
        message: str,
    ) -> Alert:
        """Insert a new alert and return the ORM instance."""
        alert = Alert(
            transaction_id=transaction_id,
            alert_type=alert_type,
            message=message,
        )
        self._db.add(alert)
        await self._db.flush()
        await self._db.refresh(alert)
        return alert

    async def get_by_transaction(self, txn_id: UUID) -> list[Alert]:
        """Return all alerts for a specific transaction."""
        result = await self._db.execute(
            select(Alert).where(Alert.transaction_id == txn_id)
        )
        return list(result.scalars().all())

    async def list_unresolved(
        self, *, skip: int = 0, limit: int = 50
    ) -> tuple[list[Alert], int]:
        """Return paginated list of unresolved alerts with total count."""
        base = select(Alert).where(Alert.resolved.is_(False))

        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        rows = await self._db.execute(
            base.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        )
        return list(rows.scalars().all()), total

    async def resolve(self, alert_id: UUID) -> bool:
        """Mark an alert as resolved. Returns True if the alert existed."""
        result = await self._db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(resolved=True)
        )
        await self._db.flush()
        return result.rowcount > 0
