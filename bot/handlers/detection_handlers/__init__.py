from aiogram import Router

from bot.handlers.detection_handlers.detection_commands import router as detection_commands_router
from bot.handlers.detection_handlers.detection_commands_handlers import router as detection_handler_router

router = Router(name=__name__)

router.include_routers(detection_commands_router,
                       detection_handler_router,
                       )
