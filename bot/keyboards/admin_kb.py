from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users")],
            [
                InlineKeyboardButton(
                    text="💰 Управление тарифами", callback_data="admin:tariffs"
                )
            ],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def admin_users_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Поиск по ID", callback_data="admin:user_by_id"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Поиск по username", callback_data="admin:user_by_username"
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")],
        ]
    )


def admin_user_actions_kb(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
    block_text = "✅ Разблокировать" if is_blocked else "🚫 Заблокировать"
    block_data = f"admin:unblock:{user_id}" if is_blocked else f"admin:block:{user_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👑 Выдать подписку", callback_data=f"admin:give_sub:{user_id}"
                )
            ],
            [InlineKeyboardButton(text=block_text, callback_data=block_data)],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:users")],
        ]
    )


def admin_give_sub_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🥉 Базовый — 30 дней",
                    callback_data=f"admin:sub:basic:30:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥈 Стандарт — 30 дней",
                    callback_data=f"admin:sub:standard:30:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🥇 Про — 30 дней", callback_data=f"admin:sub:pro:30:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад", callback_data=f"admin:user:{user_id}"
                )
            ],
        ]
    )


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")],
        ]
    )


def admin_tariffs_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎨 Стоимость генерации", callback_data="admin:edit_gen_cost"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Пакеты токенов", callback_data="admin:edit_packages"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Цены подписок", callback_data="admin:edit_sub_prices"
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")],
        ]
    )
