from aiogram import Router

from bot.db.database import async_session_factory
from bot.handlers.base_commands import router as base_commands_router
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.handlers.detection_handlers import router as common_handlers_router
from bot.middlewares.user_middleware import UserCheckMiddleware

router = Router(name=__name__)

base_commands_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
base_commands_router.message.middleware.register(UserCheckMiddleware())
common_handlers_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
common_handlers_router.message.middleware.register(UserCheckMiddleware())


router.include_routers(base_commands_router,
                       common_handlers_router)
