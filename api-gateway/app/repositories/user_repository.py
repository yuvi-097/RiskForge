"""
User repository — async data-access layer for the users table.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Encapsulates all database operations for User entities."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, *, email: str, hashed_password: str, role: str = "USER") -> User:
        """Insert a new user and return the ORM instance."""
        from app.models.user import UserRole

        user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole(role),
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by primary key."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_users(self, *, skip: int = 0, limit: int = 50) -> list[User]:
        """Return a paginated list of users."""
        result = await self._db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
