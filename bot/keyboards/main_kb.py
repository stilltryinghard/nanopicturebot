from urllib.parse import quote
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.i18n import t


def language_kb(back: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
    ]
    if back:
        rows.append(
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="main_menu")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def terms_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("read_terms_btn", lang), callback_data="read_doc:terms"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("read_privacy_btn", lang), callback_data="read_doc:privacy"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("terms_accept_btn", lang), callback_data="accept_terms"
                ),
                InlineKeyboardButton(
                    text=t("terms_decline_btn", lang), callback_data="decline_terms"
                ),
            ],
        ]
    )


def main_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("menu_generate", lang), callback_data="generate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_balance", lang), callback_data="balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_sub", lang), callback_data="subscription"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_referral", lang), callback_data="referral"
                )
            ],
            [InlineKeyboardButton(text=t("menu_help", lang), callback_data="help")],
            [
                InlineKeyboardButton(
                    text=t("menu_language", lang), callback_data="language_select"
                )
            ],
        ]
    )


def main_menu_admin_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("menu_generate", lang), callback_data="generate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_balance", lang), callback_data="balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_sub", lang), callback_data="subscription"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_referral", lang), callback_data="referral"
                )
            ],
            [InlineKeyboardButton(text=t("menu_help", lang), callback_data="help")],
            [
                InlineKeyboardButton(
                    text=t("menu_language", lang), callback_data="language_select"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("menu_admin", lang), callback_data="admin:menu"
                )
            ],
        ]
    )


def referral_kb(ref_link: str, lang: str = "ru") -> InlineKeyboardMarkup:
    share_text = quote(
        "Генерируй изображения с помощью ИИ 🎨"
        if lang == "ru"
        else "Generate images with AI 🎨"
    )
    share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={share_text}"
    copy_label = "📋 Скопировать ссылку" if lang == "ru" else "📋 Copy link"
    share_label = "📤 Поделиться" if lang == "ru" else "📤 Share"
    back_label = t("btn_back", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=copy_label, callback_data="copy_ref_link")],
            [InlineKeyboardButton(text=share_label, url=share_url)],
            [InlineKeyboardButton(text=back_label, callback_data="main_menu")],
        ]
    )


def back_to_main_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="main_menu")],
        ]
    )
