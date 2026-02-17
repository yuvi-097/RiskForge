"""
Transaction ORM model.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TransactionStatus(str, enum.Enum):
    """Lifecycle status of a financial transaction."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"


class RiskLevel(str, enum.Enum):
    """Risk classification after scoring."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Transaction(UUIDMixin, TimestampMixin, Base):
    """Represents a single financial transaction submitted for risk evaluation."""

    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction details
    amount: Mapped[float] = mapped_column(Numeric(precision=18, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    transaction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Scoring fields (populated by risk-service)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status", create_constraint=True),
        default=TransactionStatus.PENDING,
        nullable=False,
    )
    rule_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, name="risk_level", create_constraint=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="transactions")
    alerts = relationship("Alert", back_populates="transaction", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index("ix_transactions_user_id_created", "user_id", "created_at"),
        Index("ix_transactions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.id} amount={self.amount} status={self.status.value}>"
