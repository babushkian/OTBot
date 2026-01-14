from aiogram import Router

from bot.db.database import async_session_factory
from bot.handlers.area_handlers import router as area_handlers_router
from bot.handlers.base_handlers import router as base_commands_router
from bot.handlers.common_handlers import router as common_handlers_router
from bot.handlers.approve_handlers import router as approve_handlers_router
from bot.handlers.reports_handlers import router as reports_handlers_router
from bot.handlers.violation_handlers import router as violation_handlers_router

from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.middlewares.user_middleware import UserCheckMiddleware

router = Router(name=__name__)

router.include_routers(
    base_commands_router,
    common_handlers_router,
    approve_handlers_router,
    area_handlers_router,
    violation_handlers_router,
    reports_handlers_router,


)

router.message.middleware(DbSessionMiddleware(session_pool=async_session_factory))
router.callback_query.middleware(DbSessionMiddleware(session_pool=async_session_factory))
router.message.middleware(UserCheckMiddleware())
router.callback_query.middleware(UserCheckMiddleware())
