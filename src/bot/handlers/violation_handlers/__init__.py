from aiogram import Router

from bot.handlers.violation_handlers.violation_commands import router as violation_commands_router
from bot.handlers.violation_handlers.violation_commands_handlers import router as violation_commands_handlers_router

router = Router(name=__name__)

router.include_routers(violation_commands_router,
                       violation_commands_handlers_router)
