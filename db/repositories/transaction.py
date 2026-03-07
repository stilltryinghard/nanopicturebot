from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        type: str,
        amount: float,
        tokens: int,
        payment_id: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            tokens=tokens,
            payment_id=payment_id,
            status="pending",
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def update_status(self, payment_id: str, status: str) -> None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.payment_id == payment_id)
        )
        transaction = result.scalar_one_or_none()
        if transaction:
            transaction.status = status
            await self.session.commit()

    async def get_by_payment_id(self, payment_id: str) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_total_revenue(self) -> float:
        result = await self.session.execute(
            select(Transaction).where(Transaction.status == "success")
        )
        transactions = result.scalars().all()
        return sum(t.amount for t in transactions)

    async def get_revenue_by_period(self, days: int) -> float:
        since = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.status == "success",
                Transaction.created_at >= since,
            )
        )
        transactions = result.scalars().all()
        return sum(t.amount for t in transactions)
