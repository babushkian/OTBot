from aiogram import Router

from bot.handlers.approve_handlers.approve_commands import router as approve_command_router

router = Router(name=__name__)

router.include_routers(approve_command_router,
                       )
