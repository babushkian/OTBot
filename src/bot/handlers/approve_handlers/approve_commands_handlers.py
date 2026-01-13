"""Обработчики для одобрения пользователей."""

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import UserModel
from bot.logger_config import log
from bot.common_utils import verify_string_as_filename
from bot.bot_exceptions import StringInputError
from bot.repositories.user_repo import UserRepository
from bot.keyboards.common_keyboards import generate_cancel_button, generate_yes_no_keyboard
from bot.handlers.approve_handlers.states import ApproveUserStates
from bot.keyboards.inline_keyboards.approve_keyboards import user_roles_kb
from bot.keyboards.inline_keyboards.callback_factories import (
    UserRoleFactory,
    ApproveUserFactory,
    DeletedUserFactory,
    DisApproveUserFactory,
)

router = Router(name=__name__)


@router.callback_query(ApproveUserFactory.filter(), ApproveUserStates.started)
async def approve_user(callback: types.CallbackQuery, callback_data: ApproveUserFactory, state: FSMContext) -> None:
    """Обрабатывает кнопку выбранного пользователя для одобрения."""
    await callback.message.answer("Введите имя пользователя:", reply_markup=generate_cancel_button())
    await state.update_data(user_id=callback_data.id)
    await state.set_state(ApproveUserStates.name_enter)
    await callback.answer("Выбран пользователь для одобрения.")
    log.success("User {user} selected for approval", user=callback_data.id)


@router.message(ApproveUserStates.name_enter)
async def approve_user_enter_name(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает состояние ввода имени пользователя для одобрения."""
    try:
        user_name = verify_string_as_filename(str(message.text))
    except StringInputError as e:
        await message.answer(
            text=f"Неверно введёно имя пользователя. \n{e.args[0]}.\nНачать с начала? /approve", parse_mode="HTML"
        )
        log.warning(
            "Wrong input for user name: {text}, by user {message}", message=message.from_user.id, text=message.text
        )
        await state.clear()
        return
    else:
        await message.answer(text=f"Имя пользователя {user_name} записано.")
        await state.update_data(first_name=user_name)
        await message.answer("Выберите роль пользователя:", reply_markup=await user_roles_kb())
        await state.set_state(ApproveUserStates.role_enter)
        log.success("User name {user} saved in data state", user=user_name)


@router.callback_query(UserRoleFactory.filter(), ApproveUserStates.role_enter)
async def approve_user_enter_role(
    callback: types.CallbackQuery, callback_data: UserRoleFactory, state: FSMContext
) -> None:
    """Обрабатывает выбранную роль пользователя для одобрения."""
    user_role = callback_data.role
    data = await state.update_data(user_role=user_role)
    data_text = f"Пользователь: {data['first_name']}, Роль: {UserRole[data['user_role']]}"

    await callback.message.answer(
        f"Ввод данных завершен.\nВведённые данные:\n{data_text}.\nВсё верно?", reply_markup=generate_yes_no_keyboard()
    )
    await callback.answer(f"Роль пользователя: {user_role}")
    log.success("User role {role} saved in data state", role=user_role)
    await state.set_state(ApproveUserStates.completed)


@router.message(ApproveUserStates.completed, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_yes_no_response(
    message: types.Message, state: FSMContext, session: AsyncSession, group_user: UserModel
) -> None:
    """Обработчик для ответов "Да" или "Нет" при одобрении пользователя."""
    data = await state.get_data()
    if message.text == "✅ Да":
        user_id = data.pop("user_id")
        data.update({"is_approved": True})
        user_repo = UserRepository(session)
        success = await user_repo.update_user_by_id(user_id, data)
        if success:
            await message.answer(f"Данные пользователя {data['first_name']} обновлены.")
            log.success("User data {user} updated", user=data["first_name"])
        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error updating user data {user}", user=data["first_name"])
        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Заполнение отменено, для повторного вызовите команду /approve.")
        await state.clear()
        log.info("User data {user} update canceled", user=group_user.first_name)


@router.callback_query(DisApproveUserFactory.filter())
async def disapprove_user(
    callback: types.CallbackQuery,
    callback_data: ApproveUserFactory,
    session: AsyncSession,
) -> None:
    """Обрабатывает кнопку выбранного пользователя для отмены регистрации."""
    user_id = callback_data.id
    user_repo = UserRepository(session)
    update_data = {"is_approved": False, "user_role": UserRole.USER}
    await user_repo.update_user_by_id(user_id=user_id, update_data=update_data)

    await callback.message.answer("Регистрация пользователя отменена.")
    await callback.answer("Регистрация пользователя отменена.")
    log.success("User {user} registration canceled", user=user_id)


@router.callback_query(DeletedUserFactory.filter())
async def delete_user(
    callback: types.CallbackQuery,
    callback_data: DeletedUserFactory,
    session: AsyncSession,
) -> None:
    """Обрабатывает кнопку выбранного пользователя для удаления."""
    user_id = callback_data.id
    user_repo = UserRepository(session)
    await user_repo.delete_user_by_id(user_id=user_id)

    await callback.answer("Пользователь удалён из базы данных.")
    log.success("User {user} deleted from database", user=user_id)
