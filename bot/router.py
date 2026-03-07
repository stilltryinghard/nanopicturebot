from aiogram import Router
from bot.handlers import start, generate, balance, referral, admin

router = Router()

router.include_router(start.router)
router.include_router(generate.router)
router.include_router(balance.router)
router.include_router(referral.router)
router.include_router(admin.router)
