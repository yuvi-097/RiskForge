"""
Transaction repository — async data-access layer for the transactions table.
"""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import RiskLevel, Transaction, TransactionStatus


class TransactionRepository:
    """Encapsulates all database operations for Transaction entities."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs) -> Transaction:
        """Insert a new transaction and return the ORM instance."""
        txn = Transaction(**kwargs)
        self._db.add(txn)
        await self._db.flush()
        await self._db.refresh(txn)
        return txn

    async def get_by_id(self, txn_id: UUID) -> Transaction | None:
        """Fetch a single transaction by primary key."""
        result = await self._db.execute(
            select(Transaction).where(Transaction.id == txn_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Transaction], int]:
        """Return paginated transactions for a user and total count."""
        base = select(Transaction).where(Transaction.user_id == user_id)

        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        rows = await self._db.execute(
            base.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        )
        return list(rows.scalars().all()), total

    async def update_risk_scores(
        self,
        txn_id: UUID,
        *,
        rule_score: float,
        ml_score: float,
        final_score: float,
        risk_level: RiskLevel,
        status: TransactionStatus,
    ) -> None:
        """Update the scoring columns for a transaction after risk evaluation."""
        await self._db.execute(
            update(Transaction)
            .where(Transaction.id == txn_id)
            .values(
                rule_score=rule_score,
                ml_score=ml_score,
                final_score=final_score,
                risk_level=risk_level,
                status=status,
            )
        )
        await self._db.flush()
