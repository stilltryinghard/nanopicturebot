from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.generation import Generation
    from db.models.subscription import Subscription
    from db.models.transaction import Transaction
from sqlalchemy import BigInteger, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # telegram user_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Токены
    tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Онбординг
    language: Mapped[str | None] = mapped_column(String(8), nullable=True, default=None)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Реферальная система
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    generations: Mapped[list["Generation"]] = relationship(back_populates="user")
    subscription: Mapped["Subscription | None"] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
