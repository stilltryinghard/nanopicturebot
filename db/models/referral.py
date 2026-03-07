from __future__ import annotations
from sqlalchemy import BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base, TimestampMixin


class Referral(Base, TimestampMixin):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, index=True)  # кто пригласил
    referred_id: Mapped[int] = mapped_column(BigInteger, unique=True)  # кого пригласили
    bonus_paid: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # начислен ли бонус
    bonus_tokens: Mapped[int] = mapped_column(default=0)  # сколько токенов начислено
