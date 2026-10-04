from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import httpx
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, HTTPException, Request

from core.config import settings
from core.logger import logger
from db.repositories.subscription import SubscriptionRepository
from db.repositories.transaction import TransactionRepository
from db.repositories.user import UserRepository
from db.session import async_session_maker

app = FastAPI()

YUKASSA_API_URL = "https://api.yookassa.ru/v3/payments"


async def fetch_payment(payment_id: str) -> dict | None:
    """
    Спрашиваем у ЮКассы реальный статус платежа.
    Тело вебхука не аутентифицировано, поэтому верим только API.
    None — такого платежа не существует.
    """
    async with httpx.AsyncClient(
        auth=(settings.YUKASSA_SHOP_ID, settings.YUKASSA_SECRET_KEY),
        timeout=10,
    ) as client:
        r = await client.get(f"{YUKASSA_API_URL}/{payment_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def notify_user(user_id: int, plan: str | None, tokens: int) -> None:
    if plan:
        text = (
            f"✅ <b>Подписка активирована!</b>\n\n"
            f"Тариф: <b>{plan.capitalize()}</b>\nДействует 30 дней."
        )
    else:
        text = f"✅ <b>Оплата прошла!</b>\n\nНачислено <b>{tokens} токенов</b>."

    async with Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    ) as bot:
        await bot.send_message(chat_id=user_id, text=text)


@app.post("/webhook/yukassa")
async def yukassa_webhook(request: Request):
    data = await request.json()

    if data.get("event") != "payment.succeeded":
        return {"status": "ok"}

    # Из тела берём только id — всё остальное узнаём сами
    payment_id = (data.get("object") or {}).get("id")
    if not payment_id:
        return {"status": "ok"}

    try:
        payment = await fetch_payment(payment_id)
    except httpx.HTTPError:
        logger.exception(f"Webhook: не удалось проверить платёж {payment_id}")
        # 5xx — ЮКасса повторит уведомление позже
        raise HTTPException(status_code=503)

    if payment is None:
        logger.warning(f"Webhook: платёж {payment_id} не найден в ЮКассе, возможна подделка")
        return {"status": "ok"}
    if payment.get("status") != "succeeded" or not payment.get("paid"):
        return {"status": "ok"}

    async with async_session_maker() as session:
        trans_repo = TransactionRepository(session)
        user_repo = UserRepository(session)
        sub_repo = SubscriptionRepository(session)

        transaction = await trans_repo.get_by_payment_id(payment_id)
        if transaction is None:
            logger.warning(f"Webhook: платёж {payment_id} не найден в нашей базе")
            return {"status": "ok"}
        if transaction.status == "success":
            logger.info(f"Webhook: платёж {payment_id} уже обработан, пропускаем")
            return {"status": "ok"}

        # Сверяем сумму: оплачено должно быть ровно столько, сколько мы выставили
        paid = Decimal(payment["amount"]["value"])
        expected = Decimal(str(transaction.amount))
        if paid != expected:
            logger.error(
                f"Webhook: сумма {paid} != ожидаемой {expected} для платежа {payment_id}"
            )
            return {"status": "ok"}

        # Атомарно забираем платёж в обработку: из параллельных дублей
        # статус pending → success сменит только один запрос
        claimed = await trans_repo.mark_success_if_pending(payment_id)
        if claimed is None:
            logger.info(f"Webhook: платёж {payment_id} уже обработан параллельно")
            return {"status": "ok"}

        # Что начислять — берём из нашей транзакции, а не из metadata
        user_id = claimed.user_id
        tokens = claimed.tokens
        plan: str | None = None

        if claimed.type.startswith("subscription_"):
            plan = claimed.type.removeprefix("subscription_")
            await sub_repo.upsert(
                user_id=user_id,
                plan=plan,
                expires_at=datetime.now() + timedelta(days=30),  # noqa: DTZ005 — в проекте naive-время
            )
            logger.info(f"Webhook: подписка {plan} активирована для юзера {user_id}")
        else:
            await user_repo.update_tokens(user_id, amount=tokens)
            logger.info(f"Webhook: начислено {tokens} токенов юзеру {user_id}")

        # Статус и начисление — одним коммитом: упадёт начисление, откатится и статус
        await session.commit()

    try:
        await notify_user(user_id, plan, tokens)
    except Exception:  # noqa: BLE001 — граница: уведомление не должно ронять вебхук
        # Деньги уже зачислены — падение уведомления не должно ронять вебхук,
        # иначе ЮКасса будет слать его повторно
        logger.exception(f"Webhook: не удалось уведомить юзера {user_id}")

    return {"status": "ok"}