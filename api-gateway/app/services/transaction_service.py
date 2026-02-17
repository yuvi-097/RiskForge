"""
Transaction service — create transactions, check cache, and enqueue risk evaluation.
"""

import json
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionList, TransactionResponse

logger = get_logger("transaction_service")

CACHE_TTL_SECONDS = 600  # 10 minutes


class TransactionService:
    """Orchestrates transaction creation, caching, and risk-evaluation dispatch."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis | None) -> None:
        self._repo = TransactionRepository(db)
        self._redis = redis

    async def create_transaction(
        self,
        payload: TransactionCreate,
        user_id: UUID,
    ) -> TransactionResponse:
        """Create a PENDING transaction and dispatch it for risk evaluation.

        Args:
            payload: Transaction details from the client.
            user_id: Authenticated user UUID.

        Returns:
            TransactionResponse with status=PENDING.
        """
        txn_time = payload.transaction_time or datetime.now(timezone.utc)

        txn = await self._repo.create(
            user_id=user_id,
            amount=float(payload.amount),
            currency=payload.currency,
            location=payload.location,
            device_id=payload.device_id,
            ip_address=payload.ip_address,
            transaction_time=txn_time,
        )

        # Enqueue risk evaluation to the risk-service via Celery
        # Only attempt if Redis (broker) is available to avoid blocking
        if self._redis:
            try:
                celery_app.send_task(
                    "app.tasks.risk_tasks.evaluate_transaction",
                    args=[str(txn.id)],
                    queue="risk_queue",
                )
            except Exception as exc:
                logger.warning("celery_dispatch_failed", error=str(exc), transaction_id=str(txn.id))
        else:
            logger.info("skipping_risk_evaluation_no_redis", transaction_id=str(txn.id))

        logger.info(
            "transaction_created",
            transaction_id=str(txn.id),
            user_id=str(user_id),
            amount=float(txn.amount),
        )
        return TransactionResponse.model_validate(txn)

    async def get_transaction(self, txn_id: UUID, user_id: UUID) -> TransactionResponse:
        """Retrieve a transaction, checking Redis cache first.

        Args:
            txn_id: Transaction UUID.
            user_id: Requesting user's UUID (ownership check).

        Returns:
            TransactionResponse (from cache or DB).
        """
        # 1. Check cache
        cache_key = f"txn_result:{txn_id}"
        if self._redis:
            cached = await self._redis.get(cache_key)
            if cached:
                logger.info("cache_hit", transaction_id=str(txn_id))
                return TransactionResponse.model_validate_json(cached)

        # 2. DB fallback
        txn = await self._repo.get_by_id(txn_id)
        if txn is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )
        if txn.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorised to view this transaction",
            )

        response = TransactionResponse.model_validate(txn)

        # 3. Cache result if scoring is complete
        if txn.final_score is not None and self._redis:
            await self._redis.setex(
                cache_key,
                CACHE_TTL_SECONDS,
                response.model_dump_json(),
            )

        return response

    async def list_user_transactions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> TransactionList:
        """Return paginated transactions for the authenticated user."""
        items, total = await self._repo.list_by_user(user_id, skip=skip, limit=limit)
        return TransactionList(
            total=total,
            items=[TransactionResponse.model_validate(t) for t in items],
        )
