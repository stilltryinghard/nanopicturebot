from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db.models.user import User
from db.repositories.transaction import TransactionRepository
from db.repositories.subscription import SubscriptionRepository
from db.repositories.user import UserRepository
from db.session import async_session_maker
from bot.keyboards.balance_kb import (
    balance_menu_kb,
    token_packages_kb,
    subscription_plans_kb,
)
from bot.keyboards.main_kb import back_to_main_kb
from core.i18n import t

router = Router()


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
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    lang = user.language or "ru"
    _, tokens_str, amount_str = callback.data.split(":")
    tokens = int(tokens_str)
    amount = float(amount_str)

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        trans_repo = TransactionRepository(session)

        await user_repo.update_tokens(user.id, amount=tokens)
        await trans_repo.create(
            user_id=user.id,
            type="purchase",
            amount=amount,
            tokens=tokens,
            payment_id=str(uuid.uuid4()),
        )

    await callback.message.edit_text(
        text=t("bal_tokens_added", lang, tokens=str(tokens), amount=str(amount)),
        reply_markup=back_to_main_kb(lang),
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
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    lang = user.language or "ru"
    _, plan, amount_str = callback.data.split(":")
    amount = float(amount_str)

    async with async_session_maker() as session:
        sub_repo = SubscriptionRepository(session)
        trans_repo = TransactionRepository(session)

        await sub_repo.upsert(
            user_id=user.id,
            plan=plan,
            expires_at=datetime.now() + timedelta(days=30),
        )
        await trans_repo.create(
            user_id=user.id,
            type=f"subscription_{plan}",
            amount=amount,
            tokens=0,
            payment_id=str(uuid.uuid4()),
        )

    await callback.message.edit_text(
        text=t("bal_sub_activated", lang, plan=plan.capitalize(), amount=str(amount)),
        reply_markup=back_to_main_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()
