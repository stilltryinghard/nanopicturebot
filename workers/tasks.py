from __future__ import annotations
import asyncio
import json as _json
from workers.celery_app import celery_app
from core.logger import logger

POLL_INTERVAL = 5  # секунд между проверками статуса MJ
MJ_MAX_POLLS = 120  # 120 * 5с = 10 минут максимум


def get_ai_service(model: str):
    """Фабрика — возвращает нужный сервис по названию модели."""
    from services.ai.nano_banana import NanoBananaService
    from services.ai.seedream import SeedreamService
    from services.ai.midjourney import MidjourneyService

    services = {
        "nano_banana": NanoBananaService,
        "seedream": SeedreamService,
        "midjourney": MidjourneyService,
    }
    cls = services.get(model)
    if not cls:
        raise ValueError(f"Неизвестная модель: {model}")
    return cls()


async def _send_images(bot, user_id: int, images: list[bytes]) -> None:
    from aiogram.types import InputMediaPhoto, BufferedInputFile

    if len(images) == 1:
        await bot.send_photo(
            chat_id=user_id,
            photo=BufferedInputFile(images[0], filename="image.png"),
            caption="✅ Ваше изображение готово!",
        )
    else:
        media = [
            InputMediaPhoto(
                media=BufferedInputFile(img, filename=f"image_{i}.png"),
                caption="✅ Ваши изображения готовы!" if i == 0 else None,
            )
            for i, img in enumerate(images)
        ]
        await bot.send_media_group(chat_id=user_id, media=media)


async def _refund_and_notify(user_id: int, generation_id: int, cost: int) -> None:
    from db.session import async_session_maker
    from db.repositories.generation import GenerationRepository
    from db.repositories.user import UserRepository
    from aiogram import Bot
    from core.config import settings

    async with async_session_maker() as session:
        await GenerationRepository(session).update_status(generation_id, "failed")
        await UserRepository(session).update_tokens(user_id, amount=cost)

    async with Bot(token=settings.BOT_TOKEN) as bot:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ошибка при генерации. Токены возвращены на ваш баланс.",
        )
    logger.error(
        f"Генерация {generation_id} провалилась, токены {cost} возвращены юзеру {user_id}"
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_images_task(
    self,
    user_id: int,
    generation_id: int,
    model: str,
    prompt: str,
    quality: str,
    count: int,
    cost: int,
    preference: str | None = None,
):
    from celery.exceptions import MaxRetriesExceededError
    from services.ai.base import GenerationRequest
    from db.session import async_session_maker
    from db.repositories.generation import GenerationRepository
    from aiogram import Bot
    from core.config import settings

    async def _run():
        async with async_session_maker() as session:
            gen = await GenerationRepository(session).get_by_id(generation_id)
            if gen and gen.status == "done":
                logger.info(f"Генерация {generation_id} уже выполнена, пропускаем")
                return

        if model == "midjourney":
            # Только сабмитим задачу в MJ API; поллинг — отдельный таск,
            # чтобы не блокировать воркер на 10 минут
            import aiohttp
            from services.ai.midjourney import MidjourneyService

            service = MidjourneyService()
            async with aiohttp.ClientSession() as session:
                mj_task_id = await service._submit_task(session, prompt)

            poll_midjourney_task.apply_async(
                kwargs=dict(
                    mj_task_id=mj_task_id,
                    user_id=user_id,
                    generation_id=generation_id,
                    count=count,
                    cost=cost,
                ),
                countdown=POLL_INTERVAL,
            )
            logger.info(f"Midjourney задача {mj_task_id} отправлена на поллинг")
            return

        service = get_ai_service(model)
        request = GenerationRequest(
            prompt=prompt,
            quality=quality,
            count=count,
            preference=preference,
        )
        result = await service.generate(request)

        async with Bot(token=settings.BOT_TOKEN) as bot:
            await _send_images(bot, user_id, result.images)

        async with async_session_maker() as session:
            await GenerationRepository(session).update_status(generation_id, "done")

        logger.info(f"Генерация {generation_id} завершена для юзера {user_id}")

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.warning(
            f"Ошибка генерации {generation_id} (попытка {self.request.retries + 1}): {exc}"
        )
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            asyncio.run(_refund_and_notify(user_id, generation_id, cost))


@celery_app.task(bind=True, max_retries=MJ_MAX_POLLS, default_retry_delay=POLL_INTERVAL)
def poll_midjourney_task(
    self,
    mj_task_id: str,
    user_id: int,
    generation_id: int,
    count: int,
    cost: int,
):
    """
    Один опрос статуса MJ-задачи. Если не готово — Celery повторит через
    POLL_INTERVAL секунд (max MJ_MAX_POLLS раз). Воркер не блокируется.
    """
    from celery.exceptions import MaxRetriesExceededError

    async def _check_once() -> bool:
        """Возвращает True если готово, False если ещё ждём. Raises при ошибке MJ."""
        import aiohttp
        from core.config import settings

        headers = {
            "Authorization": f"Bearer {settings.MIDJOURNEY_API_KEY}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.midapi.ai/api/v1/mj/record-info?taskId={mj_task_id}",
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()

        task_data = data.get("data", {})
        success_flag = task_data.get("successFlag", 0)

        if success_flag == 1:
            result_info = task_data.get("resultInfoJson")
            if isinstance(result_info, str):
                result_info = _json.loads(result_info)
            raw_urls = (result_info or {}).get("resultUrls", [])
            urls = [
                item["resultUrl"] if isinstance(item, dict) else item
                for item in raw_urls
            ][:count]

            images: list[bytes] = []
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    async with session.get(url) as img_response:
                        images.append(await img_response.read())

            from aiogram import Bot
            from db.session import async_session_maker
            from db.repositories.generation import GenerationRepository

            async with Bot(token=settings.BOT_TOKEN) as bot:
                await _send_images(bot, user_id, images)

            async with async_session_maker() as db_session:
                await GenerationRepository(db_session).update_status(
                    generation_id, "done"
                )

            logger.info(
                f"Midjourney генерация {generation_id} завершена для юзера {user_id}"
            )
            return True

        if success_flag in (2, 3):
            error_msg = task_data.get("errorMessage", "Generation failed")
            raise Exception(f"Midjourney task failed: {error_msg}")

        # Ещё ждём
        return False

    try:
        done = asyncio.run(_check_once())
    except Exception as exc:
        logger.warning(
            f"Ошибка поллинга MJ {mj_task_id} (попытка {self.request.retries + 1}): {exc}"
        )
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            asyncio.run(_refund_and_notify(user_id, generation_id, cost))
        return

    if not done:
        logger.info(
            f"Midjourney {mj_task_id}: ждём, попытка {self.request.retries + 1}/{MJ_MAX_POLLS}"
        )
        raise self.retry(countdown=POLL_INTERVAL)


@celery_app.task
def check_low_balance():
    """
    Периодическая задача — раз в день проверяет баланс юзеров.
    Если токенов мало — отправляет напоминание. Работает батчами по 100.
    """
    LOW_BALANCE_THRESHOLD = 20
    BATCH_SIZE = 100

    async def _run():
        from db.session import async_session_maker
        from db.repositories.user import UserRepository
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from core.config import settings

        async with Bot(token=settings.BOT_TOKEN) as bot:
            offset = 0
            while True:
                async with async_session_maker() as session:
                    users = await UserRepository(session).get_low_balance_users(
                        threshold=LOW_BALANCE_THRESHOLD,
                        limit=BATCH_SIZE,
                        offset=offset,
                    )

                if not users:
                    break

                for user in users:
                    try:
                        await bot.send_message(
                            chat_id=user.id,
                            text=(
                                "⚠️ <b>Низкий баланс!</b>\n\n"
                                f"На вашем счету осталось <b>{user.tokens} токенов</b>.\n"
                                "Пополните баланс чтобы продолжить генерацию изображений 👇"
                            ),
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(
                                            text="💳 Пополнить баланс",
                                            callback_data="buy_tokens",
                                        )
                                    ]
                                ]
                            ),
                            parse_mode="HTML",
                        )
                    except Exception as e:
                        logger.warning(
                            f"Не удалось отправить уведомление юзеру {user.id}: {e}"
                        )

                offset += BATCH_SIZE

    asyncio.run(_run())
