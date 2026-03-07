from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from db.models.user import User


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(
        String(64)
    )  # purchase, referral_bonus, subscription_*
    amount: Mapped[float] = mapped_column(Float)  # сумма в рублях
    tokens: Mapped[int] = mapped_column(Integer)  # сколько токенов начислено
    payment_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )  # id платежа юкассы
    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending, success, failed

    # Relationships
    user: Mapped[User] = relationship(back_populates="transactions")
