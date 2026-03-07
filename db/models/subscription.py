from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.user import User
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base, TimestampMixin
from datetime import datetime


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True, unique=True
    )
    plan: Mapped[str] = mapped_column(String(32))  # basic, standard, pro
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscription")
