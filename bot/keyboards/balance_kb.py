from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.i18n import t


def balance_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("bal_kb_buy_tokens", lang), callback_data="buy_tokens"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("bal_kb_buy_sub", lang), callback_data="subscription"
                )
            ],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="main_menu")],
        ]
    )


async def token_packages_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    from services.settings_service import bot_settings

    packages = await bot_settings.get_token_packages()
    rows = [
        [
            InlineKeyboardButton(
                text=t(
                    "bal_kb_token_label",
                    lang,
                    tokens=str(p["tokens"]),
                    amount=str(p["amount"]),
                ),
                callback_data=f"package:{p['tokens']}:{p['amount']}",
            )
        ]
        for p in packages
    ]
    rows.append(
        [InlineKeyboardButton(text=t("btn_nav_back", lang), callback_data="balance")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def subscription_plans_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    from services.settings_service import bot_settings

    plans = await bot_settings.get_subscription_plans()
    per_month = t("bal_kb_per_month", lang)
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p['label']} — {p['amount']}₽{per_month}",
                callback_data=f"sub:{p['plan']}:{p['amount']}",
            )
        ]
        for p in plans
    ]
    rows.append(
        [InlineKeyboardButton(text=t("btn_nav_back", lang), callback_data="balance")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_kb(url: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("bal_kb_pay", lang), url=url)],
            [
                InlineKeyboardButton(
                    text=t("btn_nav_back", lang), callback_data="balance"
                )
            ],
        ]
    )
