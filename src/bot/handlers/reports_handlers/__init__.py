from aiogram import Router

from bot.handlers.reports_handlers.reports_commands import router as reports_commands_router
from bot.handlers.reports_handlers.reports_commands_handlers import router as reports_commands_handlers_router

router = Router(name=__name__)

router.include_routers(
    reports_commands_router,
    reports_commands_handlers_router,
)
