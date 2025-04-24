from bot.handlers.base_handlers import router as base_commands_router
from aiogram import Router

router = Router(name=__name__)

router.include_routers(base_commands_router,

                       )
