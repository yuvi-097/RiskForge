"""
Transaction-related Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Payload for creating a new transaction."""
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    currency: str = Field(default="USD", max_length=3)
    location: str | None = Field(default=None, max_length=256)
    device_id: str | None = Field(default=None, max_length=128)
    ip_address: str | None = Field(default=None, max_length=45)
    transaction_time: datetime | None = Field(
        default=None,
        description="Timestamp of the transaction. Defaults to server time if omitted.",
    )


class TransactionResponse(BaseModel):
    """Full transaction representation returned to clients."""
    id: UUID
    user_id: UUID
    amount: float
    currency: str
    location: str | None
    device_id: str | None
    ip_address: str | None
    transaction_time: datetime
    status: str
    rule_score: float | None
    ml_score: float | None
    final_score: float | None
    risk_level: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionList(BaseModel):
    """Paginated list of transactions."""
    total: int
    items: list[TransactionResponse]
