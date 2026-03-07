from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.i18n import t


def select_model_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🍌 Nano Banana", callback_data="model:nano_banana"
                )
            ],
            [InlineKeyboardButton(text="🌱 Seedream", callback_data="model:seedream")],
            [
                InlineKeyboardButton(
                    text="🎨 Midjourney", callback_data="model:midjourney"
                )
            ],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="main_menu")],
        ]
    )


def select_quality_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼 2K", callback_data="quality:2K")],
            [InlineKeyboardButton(text="✨ 4K", callback_data="quality:4K")],
            [
                InlineKeyboardButton(
                    text=t("btn_nav_back", lang), callback_data="generate"
                )
            ],
        ]
    )


def select_count_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣", callback_data="count:1"),
                InlineKeyboardButton(text="2️⃣", callback_data="count:2"),
                InlineKeyboardButton(text="3️⃣", callback_data="count:3"),
                InlineKeyboardButton(text="4️⃣", callback_data="count:4"),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_nav_back", lang), callback_data="generate"
                )
            ],
        ]
    )


def confirm_generation_kb(cost: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("gen_kb_confirm", lang, cost=str(cost)),
                    callback_data="confirm_generate",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("gen_kb_cancel", lang), callback_data="generate"
                )
            ],
        ]
    )


def skip_preference_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("gen_kb_skip", lang), callback_data="skip_preference"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_nav_back", lang), callback_data="generate"
                )
            ],
        ]
    )
