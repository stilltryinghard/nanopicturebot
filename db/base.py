from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
