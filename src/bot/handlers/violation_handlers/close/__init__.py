from .violation_commands import router as close_router
from .violation_commands_handlers import router as close_handlers_router
from aiogram import Router

router = Router(name = __name__)
router.include_routers(close_router, close_handlers_router)
__all__ = [router]