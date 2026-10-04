from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.balance_kb import (
    balance_menu_kb,
    payment_kb,
    subscription_plans_kb,
    token_packages_kb,
)
from core.i18n import t
from core.logger import logger
from db.models.user import User
from db.repositories.subscription import SubscriptionRepository
from db.repositories.transaction import TransactionRepository
from db.session import async_session_maker
from services.payment.yukassa import YukassaService
from services.settings_service import bot_settings

router = Router()
yukassa = YukassaService()


@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    lang = user.language or "ru"

    async with async_session_maker() as session:
        sub_repo = SubscriptionRepository(session)
        is_active = await sub_repo.is_active(user.id)
        subscription = await sub_repo.get_by_user_id(user.id)

    if is_active and subscription:
        sub_text = t(
            "bal_sub_active",
            lang,
            plan=subscription.plan.capitalize(),
            date=subscription.expires_at.strftime("%d.%m.%Y"),
        )
    else:
        sub_text = t("bal_no_sub", lang)

    await callback.message.edit_text(
        text=t("bal_title", lang, tokens=str(user.tokens), sub_text=sub_text),
        reply_markup=balance_menu_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "buy_tokens")
async def show_token_packages(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    lang = user.language or "ru"
    await callback.message.edit_text(
        text=t("bal_buy_tokens_title", lang),
        reply_markup=await token_packages_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("package:"))
async def buy_package(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message) or not callback.data:
        return
    lang = user.language or "ru"

    # В callback_data только количество токенов, цену берём из настроек:
    # callback_data можно подделать, настройкам на сервере — нет.
    try:
        tokens = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer()
        return

    packages = await bot_settings.get_token_packages()
    package = next((p for p in packages if int(p["tokens"]) == tokens), None)
    if package is None:
        await callback.answer(t("bal_package_unavailable", lang), show_alert=True)
        return
    amount = float(package["amount"])

    try:
        # SDK ЮКассы синхронный — уводим в поток, чтобы не блокировать event loop
        payment_id, url = await asyncio.to_thread(
            yukassa.create_payment,
            amount=amount,
            description=f"{tokens} токенов",
            user_id=user.id,
            tokens=tokens,
        )
    except Exception: # noqa: BLE001 — граница: любой сбой SDK → сообщение юзеру, трейс в лог
        logger.exception(f"Не удалось создать платёж для юзера {user.id}")
        await callback.answer(t("bal_payment_error", lang), show_alert=True)
        return

    # Транзакция со статусом pending (дефолт модели); вебхук переведёт её в success
    async with async_session_maker() as session:
        await TransactionRepository(session).create(
            user_id=user.id,
            type="purchase",
            amount=amount,
            tokens=tokens,
            payment_id=payment_id,
        )

    await callback.message.edit_text(
        text=t("bal_pay_prompt", lang, amount=str(amount)),
        reply_markup=payment_kb(url, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "subscription")
async def show_subscription(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    lang = user.language or "ru"
    await callback.message.edit_text(
        text=t("bal_sub_title", lang),
        reply_markup=await subscription_plans_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:"))
async def buy_subscription(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message) or not callback.data:
        return
    lang = user.language or "ru"

    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer()
        return
    plan = parts[1]

    plans = await bot_settings.get_subscription_plans()
    plan_info = next((p for p in plans if p["plan"] == plan), None)
    if plan_info is None:
        await callback.answer(t("bal_package_unavailable", lang), show_alert=True)
        return
    amount = float(plan_info["amount"])

    try:
        payment_id, url = await asyncio.to_thread(
            yukassa.create_payment,
            amount=amount,
            description=f"Подписка {plan_info['label']}",
            user_id=user.id,
            tokens=0,
            plan=plan,
        )
    except Exception: # noqa: BLE001 — граница: любой сбой SDK → сообщение юзеру, трейс в лог 
        logger.exception(f"Не удалось создать платёж подписки для юзера {user.id}")
        await callback.answer(t("bal_payment_error", lang), show_alert=True)
        return

    async with async_session_maker() as session:
        await TransactionRepository(session).create(
            user_id=user.id,
            type=f"subscription_{plan}",
            amount=amount,
            tokens=0,
            payment_id=payment_id,
        )

    await callback.message.edit_text(
        text=t("bal_pay_prompt", lang, amount=str(amount)),
        reply_markup=payment_kb(url, lang),
        parse_mode="HTML",
    )
    await callback.answer()