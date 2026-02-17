"""
Transaction API routes.

Endpoints:
    POST /transactions/       — submit a new transaction for risk evaluation
    GET  /transactions/{id}   — retrieve a single transaction (cached)
    GET  /transactions/       — list the current user's transactions
"""

from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionList, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TransactionService:
    """Build a TransactionService with injected dependencies."""
    return TransactionService(db, redis)


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    """Submit a new transaction. It will be queued for async risk evaluation."""
    return await service.create_transaction(payload, user_id=current_user.id)


@router.get("/{txn_id}", response_model=TransactionResponse)
async def get_transaction(
    txn_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    """Retrieve a transaction by ID. Returns cached result if available."""
    return await service.get_transaction(txn_id, user_id=current_user.id)


@router.get("/", response_model=TransactionList)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    """List the current user's transactions (paginated)."""
    return await service.list_user_transactions(
        user_id=current_user.id, skip=skip, limit=limit,
    )
