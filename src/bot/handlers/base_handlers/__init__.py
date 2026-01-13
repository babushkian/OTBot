from aiogram import Router

from bot.handlers.base_handlers.base_commands import router as base_command_router
from bot.handlers.base_handlers.base_comand_hendlers import router as base_command_handler_router

router = Router(name=__name__)

router.include_routers(
    base_command_router,
    base_command_handler_router,
)
