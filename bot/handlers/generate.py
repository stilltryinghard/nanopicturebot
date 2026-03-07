from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models.user import User
from db.repositories.generation import GenerationRepository
from db.repositories.user import UserRepository
from db.session import async_session_maker
from bot.keyboards.generate_kb import (
    select_model_kb,
    select_quality_kb,
    select_count_kb,
    confirm_generation_kb,
    skip_preference_kb,
)
from bot.keyboards.main_kb import back_to_main_kb
from workers.tasks import generate_images_task
from core.config import settings
from core.i18n import t

router = Router()

MODEL_NAMES = {
    "nano_banana": "🍌 Nano Banana",
    "seedream": "🌱 Seedream",
    "midjourney": "🎨 Midjourney",
}


class GenerateStates(StatesGroup):
    waiting_prompt = State()
    waiting_preference = State()
    waiting_quality = State()
    waiting_count = State()
    waiting_confirm = State()


@router.callback_query(F.data == "generate")
async def show_generate_menu(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not isinstance(callback.message, Message):
        return
    lang = user.language or "ru"
    await state.clear()
    await callback.message.edit_text(
        text=t("gen_choose_model", lang),
        reply_markup=select_model_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("model:"))
async def select_model(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    lang = user.language or "ru"
    model = callback.data.split(":")[1]
    await state.update_data(model=model)

    await callback.message.edit_text(
        text=t("gen_model_selected", lang, model=MODEL_NAMES[model]),
        reply_markup=back_to_main_kb(lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_prompt)
    await callback.answer()


@router.message(GenerateStates.waiting_prompt)
async def receive_prompt(message: Message, state: FSMContext, user: User) -> None:
    lang = user.language or "ru"
    if not message.text:
        await message.answer(t("gen_prompt_error", lang))
        return

    await state.update_data(prompt=message.text)

    await message.answer(
        text=t("gen_preference", lang),
        reply_markup=skip_preference_kb(lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_preference)


@router.message(GenerateStates.waiting_preference)
async def receive_preference(message: Message, state: FSMContext, user: User) -> None:
    if not message.text:
        return
    lang = user.language or "ru"
    await state.update_data(preference=message.text)
    await message.answer(
        text=t("gen_choose_quality", lang),
        reply_markup=select_quality_kb(lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_quality)


@router.callback_query(F.data == "skip_preference")
async def skip_preference(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not isinstance(callback.message, Message):
        return
    lang = user.language or "ru"
    await state.update_data(preference=None)
    await callback.message.edit_text(
        text=t("gen_choose_quality", lang),
        reply_markup=select_quality_kb(lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_quality)
    await callback.answer()


@router.callback_query(F.data.startswith("quality:"))
async def select_quality(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return
    lang = user.language or "ru"
    quality = callback.data.split(":")[1]
    await state.update_data(quality=quality)
    await callback.message.edit_text(
        text=t("gen_choose_count", lang),
        reply_markup=select_count_kb(lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_count)
    await callback.answer()


@router.callback_query(F.data.startswith("count:"))
async def select_count(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    if not callback.data:
        return

    lang = user.language or "ru"
    count = int(callback.data.split(":")[1])
    await state.update_data(count=count)

    data = await state.get_data()
    model = data["model"]
    quality = data["quality"]

    from services.settings_service import bot_settings

    costs = await bot_settings.get_generation_costs()
    base_cost = costs.get(quality, 10)
    cost = base_cost * count

    await state.update_data(cost=cost)

    if user.id not in settings.ADMIN_IDS and user.tokens < cost:
        await callback.message.edit_text(
            text=t(
                "gen_insufficient_tokens",
                lang,
                cost=str(cost),
                balance=str(user.tokens),
            ),
            reply_markup=back_to_main_kb(lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    cost_line = (
        t("gen_cost_free", lang)
        if user.id in settings.ADMIN_IDS
        else t("gen_cost", lang, cost=str(cost), balance=str(user.tokens))
    )
    preference_display = data.get("preference") or t("gen_preference_none", lang)
    await callback.message.edit_text(
        text=t(
            "gen_confirm",
            lang,
            model=MODEL_NAMES[model],
            prompt=data["prompt"],
            preference=preference_display,
            quality=quality,
            count=str(count),
            cost_line=cost_line,
        ),
        reply_markup=confirm_generation_kb(cost, lang),
        parse_mode="HTML",
    )
    await state.set_state(GenerateStates.waiting_confirm)
    await callback.answer()


@router.callback_query(F.data == "confirm_generate")
async def confirm_generate(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if not isinstance(callback.message, Message):
        return

    lang = user.language or "ru"
    data = await state.get_data()

    model = data["model"]
    prompt = data["prompt"]
    quality = data["quality"]
    count = data["count"]
    preference = data.get("preference")
    cost = data["cost"]

    if user.id not in settings.ADMIN_IDS and user.tokens < cost:
        await state.clear()
        await callback.message.edit_text(
            text=t(
                "gen_insufficient_tokens",
                lang,
                cost=str(cost),
                balance=str(user.tokens),
            ),
            reply_markup=back_to_main_kb(lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await state.clear()

    charged = 0 if user.id in settings.ADMIN_IDS else cost

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        if charged > 0:
            await user_repo.update_tokens(user.id, amount=-charged)

        gen_repo = GenerationRepository(session)
        generation = await gen_repo.create(
            user_id=user.id,
            model=model,
            prompt=prompt,
            quality=quality,
            count=count,
            tokens_spent=charged,
            preference=preference,
        )

    generate_images_task.delay(
        user_id=user.id,
        generation_id=generation.id,
        model=model,
        prompt=prompt,
        quality=quality,
        count=count,
        cost=charged,
        preference=preference,
    )

    await callback.message.edit_text(
        text=t("gen_started", lang),
        reply_markup=back_to_main_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()
