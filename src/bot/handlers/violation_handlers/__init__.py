from aiogram import Router
from .check import router as check_router
from .detect import router as detect_router
from .close import router as close_router


router = Router(name=__name__)
router.include_routers(check_router, detect_router, close_router )
__all__ = [router]