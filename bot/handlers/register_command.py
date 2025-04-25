"""Процесс регистрации пользователя."""
from aiogram import Router, types

router = Router(name=__name__)


@router.message(commands=["confirm"])
async def confirm_registration(message: types.Message) -> None:
    """Подтверждение регистрации определение роли и прав пользователя."""
