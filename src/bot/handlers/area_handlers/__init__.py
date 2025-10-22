from aiogram import Router

from bot.handlers.area_handlers.area_commands import router as area_router_command_router
from bot.handlers.area_handlers.area_commands_handlers import router as area_command_handlers_router

router = Router(name=__name__)

router.include_routers(area_router_command_router, area_command_handlers_router)
