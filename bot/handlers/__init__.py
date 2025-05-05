from aiogram import Router

from bot.db.database import async_session_factory
from bot.handlers.area_handlers import router as area_handlers_router
from bot.handlers.base_handlers import router as main_base_commands_router
from bot.handlers.common_handlers import router as common_handlers_router
from bot.handlers.approve_handlers import router as approve_handlers_router
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.handlers.detection_handlers import router as detection_handlers_router
from bot.middlewares.user_middleware import UserCheckMiddleware

router = Router(name=__name__)

# регистрация middleware
# common_handler
common_handlers_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
common_handlers_router.message.middleware.register(UserCheckMiddleware())

# base_commands handler
main_base_commands_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
main_base_commands_router.message.middleware.register(UserCheckMiddleware())

# approve_handler
approve_handlers_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
approve_handlers_router.callback_query.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
approve_handlers_router.message.middleware.register(UserCheckMiddleware())

# ara_handler
area_handlers_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
area_handlers_router.callback_query.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
area_handlers_router.message.middleware.register(UserCheckMiddleware())

# detection_handler
detection_handlers_router.message.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
detection_handlers_router.callback_query.middleware.register(DbSessionMiddleware(session_pool=async_session_factory))
detection_handlers_router.message.middleware.register(UserCheckMiddleware())
detection_handlers_router.callback_query.middleware.register(UserCheckMiddleware())

router.include_routers(
    main_base_commands_router,
    common_handlers_router,
    approve_handlers_router,
    area_handlers_router,
    detection_handlers_router,
)
