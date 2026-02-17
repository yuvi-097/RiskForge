"""
Alert-related Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Single alert representation."""
    id: UUID
    transaction_id: UUID
    alert_type: str
    message: str
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertList(BaseModel):
    """Paginated list of alerts."""
    total: int
    items: list[AlertResponse]
