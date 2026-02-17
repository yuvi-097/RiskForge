"""
Authentication service — registration, login, and token issuance.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, UserCreate, UserResponse

logger = get_logger("auth_service")


class AuthService:
    """Orchestrates user registration and authentication workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def register(self, payload: UserCreate) -> UserResponse:
        """Register a new user.

        Args:
            payload: UserCreate schema with email + password.

        Returns:
            UserResponse with the newly created user.

        Raises:
            HTTPException 409 if the email is already registered.
        """
        existing = await self._repo.get_by_email(payload.email)
        if existing:
            logger.warning("registration_failed", email=payload.email, reason="duplicate")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed = hash_password(payload.password)
        user = await self._repo.create(email=payload.email, hashed_password=hashed)
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> Token:
        """Authenticate a user and return a JWT.

        Args:
            email: User email.
            password: Plain-text password.

        Returns:
            Token schema with access_token.

        Raises:
            HTTPException 401 on invalid credentials.
        """
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("login_failed", email=email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            logger.warning("login_inactive_user", email=email)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        token = create_access_token(subject=user.id, extra={"role": user.role.value})
        logger.info("login_success", user_id=str(user.id), email=user.email)
        return Token(access_token=token)
