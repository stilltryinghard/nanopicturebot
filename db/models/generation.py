from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.user import User
from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base, TimestampMixin


class Generation(Base, TimestampMixin):
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    model: Mapped[str] = mapped_column(String(32))  # nano_banana, seedream, midjourney
    prompt: Mapped[str] = mapped_column(String(2048))
    preference: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    quality: Mapped[str] = mapped_column(String(4))  # 2K, 4K
    count: Mapped[int] = mapped_column(Integer)  # 1-4
    tokens_spent: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending, done, failed

    # Relationships
    user: Mapped[User] = relationship(back_populates="generations")
