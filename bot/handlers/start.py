from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from core.config import settings
from core.i18n import t
from services.docs_service import get_privacy_policy, get_terms_of_service
from db.session import async_session_maker
from db.models.user import User
from db.repositories.user import UserRepository
from db.repositories.referral import ReferralRepository
from bot.keyboards.main_kb import (
    language_kb,
    terms_kb,
    main_menu_kb,
    main_menu_admin_kb,
    back_to_main_kb,
)

router = Router()


def get_welcome_text(user: User) -> str:
    lang = user.language or "ru"
    return t("welcome", lang, name=user.full_name, tokens=str(user.tokens))


def get_main_kb(user_id: int, lang: str):
    if user_id in settings.ADMIN_IDS:
        return main_menu_admin_kb(lang)
    return main_menu_kb(lang)


def _terms_text(lang: str) -> str:
    return t("terms_text", lang)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    if not message.from_user:
        return

    args = message.text.split() if message.text else []
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referred_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user, is_new = await user_repo.get_or_create(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            referred_by=referred_by,
        )

        if referred_by and referred_by != message.from_user.id:
            ref_repo = ReferralRepository(session)
            existing_ref = await ref_repo.get_by_referred(message.from_user.id)

            if not existing_ref:
                await ref_repo.create(
                    referrer_id=int(referred_by),
                    referred_id=message.from_user.id,
                )
                await user_repo.update_tokens(
                    int(referred_by), amount=settings.REFERRAL_BONUS_TOKENS
                )
                await user_repo.update_referral_count(int(referred_by))

        user = await user_repo.get_by_id(message.from_user.id) or user

    # ── Онбординг ──────────────────────────────────────────────────────────
    if not user.terms_accepted:
        if not user.language:
            # Шаг 1: выбор языка (текст на двух языках сразу)
            await message.answer(
                text=t("choose_language", "default"),
                reply_markup=language_kb(),
                parse_mode="HTML",
            )
        else:
            # Язык уже выбран, но terms не приняты — показываем terms
            await message.answer(
                text=_terms_text(user.language),
                reply_markup=terms_kb(user.language),
                parse_mode="HTML",
            )
        return

    # ── Главное меню ───────────────────────────────────────────────────────
    lang = user.language or "ru"
    await message.answer(
        text=get_welcome_text(user),
        reply_markup=get_main_kb(message.from_user.id, lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "language_select")
async def show_language_select(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    lang = user.language or "ru"
    await callback.message.edit_text(
        text=t("language_select_title", lang),
        reply_markup=language_kb(back=True, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    lang = callback.data.split(":")[1]  # type: ignore[union-attr]

    async with async_session_maker() as session:
        await UserRepository(session).set_language(user.id, lang)

    if user.terms_accepted:
        # Онбординг пройден — просто обновляем язык и возвращаем в меню
        user.language = lang
        await callback.message.edit_text(
            text=get_welcome_text(user),
            reply_markup=get_main_kb(callback.from_user.id, lang),  # type: ignore[union-attr]
            parse_mode="HTML",
        )
    else:
        # Онбординг не пройден — шаг 2: принятие соглашения
        await callback.message.edit_text(
            text=_terms_text(lang),
            reply_markup=terms_kb(lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "accept_terms")
async def accept_terms(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    async with async_session_maker() as session:
        await UserRepository(session).accept_terms(user.id)

    lang = user.language or "ru"
    # Обновляем локальный объект — get_welcome_text использует user.tokens
    user.terms_accepted = True

    await callback.message.edit_text(
        text=get_welcome_text(user),
        reply_markup=get_main_kb(callback.from_user.id, lang),  # type: ignore[union-attr]
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "decline_terms")
async def decline_terms(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    lang = user.language or "ru"
    await callback.message.edit_text(
        text=t("terms_declined", lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("read_doc:"))
async def read_document(callback: CallbackQuery, user: User) -> None:
    """Отправляет текст документа (страницами если длинный)."""
    doc_type = (callback.data or "").split(":")[1]
    pages = get_privacy_policy() if doc_type == "privacy" else get_terms_of_service()

    for page in pages:
        await callback.message.answer(text=page)  # type: ignore[union-attr]

    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(
    callback: CallbackQuery, user: User, state: FSMContext
) -> None:
    await state.clear()

    if not isinstance(callback.message, Message):
        return

    if not callback.from_user:
        return

    lang = user.language or "ru"
    await callback.message.edit_text(
        text=get_welcome_text(user),
        reply_markup=get_main_kb(callback.from_user.id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    lang = user.language or "ru"
    if lang == "en":
        text = (
            "ℹ️ <b>Help</b>\n\n"
            "<b>Tokens</b> — the bot's internal currency.\n"
            "Spent on each generation.\n\n"
            "<b>Generation cost:</b>\n"
            "• 2K — 10 tokens per image\n"
            "• 4K — 20 tokens per image\n\n"
            "<b>Subscription</b> gives queue priority\n"
            "and bonus tokens every month.\n\n"
            "<b>Referral program:</b>\n"
            "Invite friends and earn 50 tokens\n"
            "for each new user!"
        )
    else:
        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "<b>Токены</b> — внутренняя валюта бота.\n"
            "Тратятся при каждой генерации.\n\n"
            "<b>Стоимость генерации:</b>\n"
            "• 2K — 10 токенов за изображение\n"
            "• 4K — 20 токенов за изображение\n\n"
            "<b>Подписка</b> даёт приоритет в очереди\n"
            "и бонусные токены каждый месяц.\n\n"
            "<b>Реферальная программа:</b>\n"
            "Приглашай друзей и получай 50 токенов\n"
            "за каждого нового пользователя!"
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=back_to_main_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(StateFilter(None))
async def any_message(message: Message) -> None:
    """Ловим сообщения только когда нет активного FSM состояния."""
    if not message.from_user:
        return

    async with async_session_maker() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(message.from_user.id)

    if not user:
        await message.answer("👋 Нажми /start чтобы начать.")
        return

    if not user.terms_accepted:
        lang = user.language or "ru"
        await message.answer(t("not_onboarded", lang))
        return

    lang = user.language or "ru"
    await message.answer(
        text=get_welcome_text(user),
        reply_markup=get_main_kb(message.from_user.id, lang),
        parse_mode="HTML",
    )
