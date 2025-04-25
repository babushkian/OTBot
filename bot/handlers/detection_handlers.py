"""Общие команды."""

from aiogram import F, Router, types

from bot.repositories.user_repo import UserModel

router = Router(name=__name__)


@router.message(F.text == "det")  # TODO для тестов
@router.message(F.photo)
async def detect_violation(message: types.Message, user: UserModel) -> None:
    """Запуск процесса обнаружения нарушений."""

    # print(user)
    # print("!!!!!!")
