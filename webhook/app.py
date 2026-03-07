from __future__ import annotations
from fastapi import FastAPI, Request
from core.config import settings
from core.logger import logger

app = FastAPI()


@app.post("/webhook/yukassa")
async def yukassa_webhook(request: Request):
    data = await request.json()
    logger.info(f"Webhook received: {data}")

    event = data.get("event")
    if event != "payment.succeeded":
        return {"status": "ok"}

    payment_obj = data.get("object", {})
    payment_id = payment_obj.get("id")
    metadata = payment_obj.get("metadata", {})
    user_id = metadata.get("user_id")
    tokens = int(metadata.get("tokens", 0))
    plan = metadata.get("plan")  # есть только у подписок

    if not user_id:
        logger.warning("Webhook: нет user_id в metadata")
        return {"status": "ok"}

    user_id = int(user_id)

    from db.session import async_session_maker
    from db.repositories.user import UserRepository
    from db.repositories.transaction import TransactionRepository
    from db.repositories.subscription import SubscriptionRepository
    from datetime import datetime, timedelta

    # Дедупликация: не обрабатываем уже успешные платежи
    async with async_session_maker() as session:
        trans_repo = TransactionRepository(session)
        existing = await trans_repo.get_by_payment_id(payment_id)
        if existing and existing.status == "success":
            logger.info(f"Webhook: платёж {payment_id} уже обработан, пропускаем")
            return {"status": "ok"}

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        trans_repo = TransactionRepository(session)
        sub_repo = SubscriptionRepository(session)

        if plan:
            # Подписка
            await sub_repo.create(
                user_id=user_id,
                plan=plan,
                expires_at=datetime.now() + timedelta(days=30),
            )
            logger.info(f"Webhook: подписка {plan} активирована для юзера {user_id}")
        else:
            # Пакет токенов
            await user_repo.update_tokens(user_id, amount=tokens)
            logger.info(f"Webhook: начислено {tokens} токенов юзеру {user_id}")

        await trans_repo.update_status(payment_id, "success")

    # Уведомляем юзера
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    async with Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    ) as bot:
        if plan:
            text = f"✅ <b>Подписка активирована!</b>\n\nТариф: <b>{plan.capitalize()}</b>\nДействует 30 дней."
        else:
            text = f"✅ <b>Оплата прошла!</b>\n\nНачислено <b>{tokens} токенов</b>."
        await bot.send_message(chat_id=user_id, text=text)

    return {"status": "ok"}
