"""Команды редактирования масте нарушения."""
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.config import settings
from bot.db.models import UserModel
from logger_config import log
from bot.repositories.area_repo import AreaRepository
from bot.handlers.area_handlers.states import AreaAddOrUpdateStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import AreaDeleteFactory, AreaSelectFactory

router = Router(name=__name__)


@router.message(Command("area"))
async def area_updating(message: types.Message,
                        group_user: UserModel,
                        session: AsyncSession,
                        state: FSMContext) -> None:
    """Запуск добавление/редактирование места нарушения."""
    if message.from_user.id not in settings.SUPER_USERS_TG_ID or group_user.user_role != UserRole.ADMIN:
        return

    area_repo = AreaRepository(session)
    areas = await area_repo.get_all_areas()

    areas_to_kb = [{"area_name": area.name, "id": area.id} for area in areas] if areas else []
    areas_to_kb.append({"area_name": "Добавить новое место", "id": 0})

    areas_keyboard = await create_keyboard(items=tuple(areas_to_kb), text_key="area_name",
                                           callback_factory=AreaSelectFactory)

    await message.reply("Выберите место нарушения для редактирования:", reply_markup=areas_keyboard)
    await state.set_state(AreaAddOrUpdateStates.start)
    log.debug("Area updating process started by {user}", user=group_user.first_name)


@router.message(Command("delarea"))
async def delete_command(message: types.Message,
                         session: AsyncSession,
                         group_user: UserModel) -> None:
    """Удаление места нарушения администратором."""
    if message.from_user.id not in settings.SUPER_USERS_TG_ID or group_user.user_role != UserRole.ADMIN:
        return

    area_repo = AreaRepository(session)
    areas = await area_repo.get_all_areas()

    areas_to_kb = [{"area_name": area.name, "id": area.id} for area in areas] if areas else []

    areas_keyboard = await create_keyboard(items=tuple(areas_to_kb), text_key="area_name",
                                           callback_factory=AreaDeleteFactory)

    await message.reply("Выберите место нарушения для удаления:", reply_markup=areas_keyboard)
