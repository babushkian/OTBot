from aiogram import Router
from .commands import router as detect_router
from .command_handlers import router as detect_handle_router
from .light_command_handler import router as light_detect_handle_router
router = Router(name=__name__)
router.include_routers(detect_router, detect_handle_router, light_detect_handle_router)
__all__ = [router]