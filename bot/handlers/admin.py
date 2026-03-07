from __future__ import annotations
import asyncio
from core.logger import logger
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models.user import User
from db.repositories.user import UserRepository
from db.repositories.subscription import SubscriptionRepository
from db.repositories.generation import GenerationRepository
from db.repositories.transaction import TransactionRepository
from db.session import async_session_maker
from bot.keyboards.admin_kb import (
    admin_menu_kb,
    admin_users_kb,
    admin_user_actions_kb,
    admin_give_sub_kb,
    admin_back_kb,
    admin_tariffs_kb,
)
from core.config import settings

router = Router()


class IsAdmin(Filter):
    """Фильтр — пропускает только админов."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        from_user = event.from_user
        if not from_user:
            return False
        return from_user.id in settings.ADMIN_IDS


class IsOwner(Filter):
    """Фильтр — пропускает только владельца бота."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        from_user = event.from_user
        if not from_user:
            return False
        return from_user.id == settings.OWNER_ID


class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_username = State()
    waiting_broadcast = State()
    waiting_broadcast_confirm = State()
    waiting_gen_cost_2k = State()
    waiting_gen_cost_4k = State()
    waiting_package_edit = State()
    waiting_sub_price_edit = State()


# Применяем фильтр ко всему роутеру
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin:menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await state.clear()
    await callback.message.edit_text(
        text="⚙️ <b>Админ-панель</b>",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        gen_repo = GenerationRepository(session)
        trans_repo = TransactionRepository(session)
        sub_repo = SubscriptionRepository(session)

        users = await user_repo.get_all()
        counts_by_model = await gen_repo.count_by_model()
        revenue_total = await trans_repo.get_total_revenue()
        revenue_month = await trans_repo.get_revenue_by_period(days=30)
        revenue_week = await trans_repo.get_revenue_by_period(days=7)
        active_subs = await sub_repo.get_active_count()

    total_users = len(users)
    blocked = sum(1 for u in users if u.is_blocked)
    paid_users = sum(1 for u in users if u.tokens > 0 or u.referral_count > 0)

    # Конверсия — юзеры у которых были транзакции / все юзеры
    conversion = (paid_users / total_users * 100) if total_users > 0 else 0

    gen_text = (
        "\n".join(f"  • {model}: {count}" for model, count in counts_by_model.items())
        or "  • Нет данных"
    )

    await callback.message.edit_text(
        text=(
            "📊 <b>Статистика</b>\n\n"
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🚫 Заблокировано: <b>{blocked}</b>\n"
            f"👑 Активных подписок: <b>{active_subs}</b>\n\n"
            f"🎨 Генерации по моделям:\n{gen_text}\n\n"
            f"💰 Доход всего: <b>{revenue_total:.2f}₽</b>\n"
            f"💰 Доход за месяц: <b>{revenue_month:.2f}₽</b>\n"
            f"💰 Доход за неделю: <b>{revenue_week:.2f}₽</b>\n\n"
            f"📈 Конверсия в платных: <b>{conversion:.1f}%</b>"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        text="👥 <b>Управление пользователями</b>",
        reply_markup=admin_users_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:user_by_id")
async def ask_user_id(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        text="🔍 Введи Telegram ID пользователя:",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_user_id)
    await callback.answer()


@router.message(AdminStates.waiting_user_id)
async def search_user_by_id(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Введи числовой ID.")
        return

    user_id = int(message.text)
    await state.clear()

    async with async_session_maker() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден.", reply_markup=admin_back_kb())
        return

    await message.answer(
        text=_user_info_text(user),
        reply_markup=admin_user_actions_kb(user.id, user.is_blocked),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin:block:"))
async def block_user(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    user_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        repo = UserRepository(session)
        await repo.block(user_id, blocked=True)
        user = await repo.get_by_id(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден.")
        return

    await callback.message.edit_text(
        text=_user_info_text(user),
        reply_markup=admin_user_actions_kb(user.id, user.is_blocked),
        parse_mode="HTML",
    )
    await callback.answer("🚫 Пользователь заблокирован.")


@router.callback_query(F.data.startswith("admin:unblock:"))
async def unblock_user(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    user_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        repo = UserRepository(session)
        await repo.block(user_id, blocked=False)
        user = await repo.get_by_id(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден.")
        return

    await callback.message.edit_text(
        text=_user_info_text(user),
        reply_markup=admin_user_actions_kb(user.id, user.is_blocked),
        parse_mode="HTML",
    )
    await callback.answer("✅ Пользователь разблокирован.")


@router.callback_query(F.data.startswith("admin:user:"))
async def show_user_actions(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return
    user_id = int(callback.data.split(":")[2])
    async with async_session_maker() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)
    if not user:
        await callback.answer("❌ Пользователь не найден.")
        return
    await callback.message.edit_text(
        text=_user_info_text(user),
        reply_markup=admin_user_actions_kb(user.id, user.is_blocked),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:give_sub:"))
async def give_sub_menu(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    user_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        text="👑 Выбери тариф подписки:",
        reply_markup=admin_give_sub_kb(user_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sub:"))
async def give_subscription(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    # admin:sub:plan:days:user_id
    parts = callback.data.split(":")
    plan = parts[2]
    days = int(parts[3])
    user_id = int(parts[4])

    expires_at = datetime.now() + timedelta(days=days)

    async with async_session_maker() as session:
        repo = SubscriptionRepository(session)
        await repo.upsert(user_id=user_id, plan=plan, expires_at=expires_at)

    await callback.message.edit_text(
        text=f"✅ Подписка <b>{plan}</b> выдана на {days} дней.",
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def ask_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        text=(
            "📢 <b>Рассылка</b>\n\n"
            "Отправь сообщение для рассылки.\n"
            "Поддерживается текст, фото, видео с подписью.\n\n"
            "<i>Просто отправь мне сообщение которое хочешь разослать</i>"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()


@router.message(AdminStates.waiting_broadcast)
async def preview_broadcast(message: Message, state: FSMContext) -> None:
    # Сохраняем message_id и chat_id для последующей пересылки
    await state.update_data(
        broadcast_message_id=message.message_id,
        broadcast_chat_id=message.chat.id,
    )

    async with async_session_maker() as session:
        repo = UserRepository(session)
        users = await repo.get_all()

    total = len([u for u in users if not u.is_blocked])

    await message.answer(
        text=(
            "👁 <b>Предпросмотр рассылки выше ☝️</b>\n\n"
            f"📊 Будет отправлено: <b>{total}</b> пользователям\n\n"
            "Подтверди отправку:"
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Отправить", callback_data="admin:broadcast_confirm"
                    )
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:menu")],
            ]
        ),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_broadcast_confirm)


@router.callback_query(F.data == "admin:broadcast_confirm")
async def send_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.bot:
        return

    data = await state.get_data()
    await state.clear()

    broadcast_message_id = data.get("broadcast_message_id")
    broadcast_chat_id = data.get("broadcast_chat_id")

    if not broadcast_message_id or not broadcast_chat_id:
        await callback.answer("❌ Ошибка — сообщение не найдено.")
        return

    async with async_session_maker() as session:
        repo = UserRepository(session)
        users = await repo.get_all()

    active_users = [u for u in users if not u.is_blocked]

    await callback.message.edit_text(
        text=f"⏳ Отправляю рассылку {len(active_users)} пользователям...",
    )

    success = 0
    failed = 0

    for user in active_users:
        try:
            await callback.bot.copy_message(
                chat_id=user.id,
                from_chat_id=broadcast_chat_id,
                message_id=broadcast_message_id,
            )
            success += 1
            # Пауза чтобы не словить флуд от Telegram
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning(f"Не удалось отправить рассылку юзеру {user.id}: {e}")
            failed += 1

    await callback.message.edit_text(
        text=(
            f"📢 <b>Рассылка завершена</b>\n\n"
            f"✅ Отправлено: <b>{success}</b>\n"
            f"❌ Ошибок: <b>{failed}</b>"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


def _user_info_text(user: User) -> str:
    return (
        f"👤 <b>Пользователь</b>\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username or 'нет'}\n"
        f"Токены: {user.tokens}\n"
        f"Рефералов: {user.referral_count}\n"
        f"Заблокирован: {'да' if user.is_blocked else 'нет'}"
    )


@router.callback_query(F.data == "admin:user_by_username")
async def ask_username(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        text="🔍 Введи username пользователя (с @ или без):",
        reply_markup=admin_back_kb(),
    )
    await state.set_state(AdminStates.waiting_username)
    await callback.answer()


@router.message(AdminStates.waiting_username)
async def search_user_by_username(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    await state.clear()

    async with async_session_maker() as session:
        repo = UserRepository(session)
        user = await repo.get_by_username(message.text)

    if not user:
        await message.answer("❌ Пользователь не найден.", reply_markup=admin_back_kb())
        return

    await message.answer(
        text=_user_info_text(user),
        reply_markup=admin_user_actions_kb(user.id, user.is_blocked),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:tariffs")
async def admin_tariffs(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        return
    from services.settings_service import bot_settings

    costs = await bot_settings.get_generation_costs()
    plans = await bot_settings.get_subscription_plans()
    packages = await bot_settings.get_token_packages()

    packages_text = "\n".join(
        f"  • {p['tokens']} токенов — {p['amount']}₽" for p in packages
    )
    plans_text = "\n".join(f"  • {p['label']} — {p['amount']}₽/мес" for p in plans)

    await callback.message.edit_text(
        text=(
            "💰 <b>Управление тарифами</b>\n\n"
            f"🎨 <b>Стоимость генерации:</b>\n"
            f"  • 2K — {costs['2K']} токенов\n"
            f"  • 4K — {costs['4K']} токенов\n\n"
            f"💎 <b>Пакеты токенов:</b>\n{packages_text}\n\n"
            f"👑 <b>Подписки:</b>\n{plans_text}"
        ),
        reply_markup=admin_tariffs_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:edit_gen_cost")
async def edit_gen_cost(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    from services.settings_service import bot_settings

    costs = await bot_settings.get_generation_costs()
    await callback.message.edit_text(
        text=(
            f"🎨 <b>Стоимость генерации</b>\n\n"
            f"Сейчас: 2K = {costs['2K']} токенов, 4K = {costs['4K']} токенов\n\n"
            "Введи новые значения в формате:\n"
            "<code>10 20</code>\n"
            "(сначала 2K, потом 4K через пробел)"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_gen_cost_2k)
    await callback.answer()


@router.message(AdminStates.waiting_gen_cost_2k)
async def save_gen_cost(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    parts = message.text.strip().split()
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await message.answer(
            "❌ Неверный формат. Введи два числа через пробел: <code>10 20</code>",
            parse_mode="HTML",
        )
        return

    from services.settings_service import bot_settings

    await bot_settings.set_generation_costs({"2K": int(parts[0]), "4K": int(parts[1])})
    await state.clear()
    await message.answer(
        text=f"✅ Стоимость обновлена: 2K = {parts[0]} токенов, 4K = {parts[1]} токенов",
        reply_markup=admin_tariffs_kb(),
    )


@router.callback_query(F.data == "admin:edit_packages")
async def edit_packages(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    from services.settings_service import bot_settings

    packages = await bot_settings.get_token_packages()
    packages_text = "\n".join(f"{p['tokens']} {p['amount']}" for p in packages)
    await callback.message.edit_text(
        text=(
            "💎 <b>Пакеты токенов</b>\n\n"
            "Введи пакеты в формате (каждый с новой строки):\n"
            "<code>токены цена</code>\n\n"
            "Пример:\n"
            "<code>100 99\n300 249\n700 499\n1500 999</code>\n\n"
            f"Сейчас:\n<code>{packages_text}</code>"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_package_edit)
    await callback.answer()


@router.message(AdminStates.waiting_package_edit)
async def save_packages(message: Message, state: FSMContext) -> None:
    if not message.text:
        return
    try:
        packages = []
        for line in message.text.strip().splitlines():
            tokens, amount = line.strip().split()
            packages.append({"tokens": int(tokens), "amount": int(amount)})
    except Exception:
        await message.answer("❌ Неверный формат. Проверь и попробуй снова.")
        return

    from services.settings_service import bot_settings

    await bot_settings.set_token_packages(packages)
    await state.clear()
    await message.answer(
        "✅ Пакеты токенов обновлены!", reply_markup=admin_tariffs_kb()
    )


@router.callback_query(F.data == "admin:edit_sub_prices")
async def edit_sub_prices(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    from services.settings_service import bot_settings

    plans = await bot_settings.get_subscription_plans()
    plans_text = "\n".join(f"{p['plan']} {p['amount']}" for p in plans)
    await callback.message.edit_text(
        text=(
            "👑 <b>Цены подписок</b>\n\n"
            "Введи тарифы в формате (каждый с новой строки):\n"
            "<code>план цена</code>\n\n"
            "Доступные планы: basic, standard, pro\n\n"
            "Пример:\n"
            "<code>basic 299\nstandard 599\npro 999</code>\n\n"
            f"Сейчас:\n<code>{plans_text}</code>"
        ),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_sub_price_edit)
    await callback.answer()


@router.message(Command("maintenance"), IsOwner())
async def toggle_maintenance(message: Message) -> None:
    import redis.asyncio as aioredis

    r = aioredis.from_url(settings.REDIS_URL)
    is_on = await r.get("maintenance_mode")
    if is_on:
        await r.delete("maintenance_mode")
        await message.answer(
            "✅ Режим обслуживания <b>выключен</b> — бот работает в штатном режиме.",
            parse_mode="HTML",
        )
        logger.info("Maintenance mode OFF")
    else:
        await r.set("maintenance_mode", "1")
        await message.answer(
            "🔴 Режим обслуживания <b>включён</b> — пользователи видят сообщение о техработах.",
            parse_mode="HTML",
        )
        logger.info("Maintenance mode ON")
    await r.aclose()


@router.message(AdminStates.waiting_sub_price_edit)
async def save_sub_prices(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    labels = {"basic": "🥉 Базовый", "standard": "🥈 Стандарт", "pro": "🥇 Про"}

    try:
        plans = []
        for line in message.text.strip().splitlines():
            plan, amount = line.strip().split()
            if plan not in labels:
                raise ValueError(f"Неизвестный план: {plan}")
            plans.append({"plan": plan, "amount": int(amount), "label": labels[plan]})
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}. Проверь формат и попробуй снова.")
        return

    from services.settings_service import bot_settings

    await bot_settings.set_subscription_plans(plans)
    await state.clear()
    await message.answer("✅ Цены подписок обновлены!", reply_markup=admin_tariffs_kb())
