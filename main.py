import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonCommands
from aiogram.client.default import DefaultBotProperties
from bot.router import router
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from core.config import settings
from core.logger import logger


async def on_startup(bot: Bot) -> None:
    logger.info("Миграции применены")

    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="🏠 Главное меню"),
        ]
    )

    await bot.set_my_description(
        description=(
            "🎨 Бот для генерации изображений с помощью нейросетей!\n\n"
            "🍌 Nano Banana\n"
            "🌱 Seedream\n"
            "🎨 Midjourney\n\n"
            "Нажми /start чтобы начать!"
        )
    )

    await bot.set_my_short_description(
        short_description="Генерация изображений с помощью AI 🎨"
    )

    me = await bot.get_me()
    logger.info(f"Бот запущен: @{me.username}")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Бот остановлен")


async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))

    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Запуск бота...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
