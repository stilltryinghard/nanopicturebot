from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db.models.user import User
from db.repositories.referral import ReferralRepository
from db.session import async_session_maker
from bot.keyboards.main_kb import referral_kb
from core.config import settings

router = Router()


@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    async with async_session_maker() as session:
        repo = ReferralRepository(session)
        referrals = await repo.get_by_referrer(user.id)

    paid_count = sum(1 for r in referrals if r.bonus_paid)
    total_bonus = len(referrals) * settings.REFERRAL_BONUS_TOKENS

    bot_info = await callback.bot.get_me()  # type: ignore
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
    lang = user.language or "ru"

    if lang == "en":
        text = (
            "🔗 <b>Referral Program</b>\n\n"
            "Invite friends and earn <b>50 tokens</b> "
            "for each new user!\n\n"
            f"👥 <b>Invited:</b> {user.referral_count}\n"
            f"✅ <b>Made a purchase:</b> {paid_count}\n"
            f"🎁 <b>Tokens earned:</b> {total_bonus}\n\n"
            f"🔗 <b>Your link:</b>\n"
            f"<code>{ref_link}</code>"
        )
    else:
        text = (
            "🔗 <b>Реферальная программа</b>\n\n"
            "Приглашай друзей и получай <b>50 токенов</b> "
            "за каждого нового пользователя!\n\n"
            f"👥 <b>Приглашено:</b> {user.referral_count}\n"
            f"✅ <b>Оплатили:</b> {paid_count}\n"
            f"🎁 <b>Заработано токенов:</b> {total_bonus}\n\n"
            f"🔗 <b>Твоя ссылка:</b>\n"
            f"<code>{ref_link}</code>"
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=referral_kb(ref_link, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "copy_ref_link")
async def copy_ref_link(callback: CallbackQuery, user: User) -> None:
    bot_info = await callback.bot.get_me()  # type: ignore
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
    lang = user.language or "ru"
    caption = "👆 Нажми чтобы скопировать" if lang == "ru" else "👆 Tap to copy"
    await callback.message.answer(  # type: ignore
        text=f"<code>{ref_link}</code>\n\n<i>{caption}</i>",
        parse_mode="HTML",
    )
    await callback.answer()
