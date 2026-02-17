"""
User-related Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Payload for login (also used by OAuth2 password form)."""
    email: EmailStr
    password: str


# ── Responses ─────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user representation."""
    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT claims."""
    sub: str
    exp: int | None = None
    role: str | None = None
