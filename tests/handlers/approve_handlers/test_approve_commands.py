"""Тесты для обработчиков для одобрения и блокировки пользователей."""
from typing import Any, NewType

import pytest

from pytest_mock import MockType, MockerFixture
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from bot.enums import UserRole
from bot.constants import SUPER_USERS_TG_ID
from bot.handlers.approve_handlers import approve_commands

FakeUsers = NewType("FakeUsers", list[dict[str, Any]])

@pytest.fixture
def mock_message(mocker: MockerFixture) -> MockType:
    """Фейковый объект сообщения в телеграм."""
    message = mocker.Mock(spec=Message)
    message.reply = mocker.AsyncMock()
    message.bot.get_chat_member = mocker.AsyncMock()
    return message


@pytest.fixture
def mock_user_repo(mocker: MockerFixture) -> MockType:
    return mocker.Mock()


@pytest.fixture
def fake_users() -> FakeUsers:
    return FakeUsers([
        {"id": 1, "first_name": "John", "phone_number": "123", "telegram_id": 1001, "is_approved": False},
        {"id": 2, "first_name": "Jane", "phone_number": "456", "telegram_id": 1002, "is_approved": False},
        {"id": 3, "first_name": "Joban", "phone_number": "1458", "telegram_id": 1003, "is_approved": True},
    ])


@pytest.fixture
def mock_create_keyboard(mocker):
    return mocker.patch("bot.handlers.approve_handlers.approve_commands.create_keyboard", new_callable=mocker.AsyncMock)


@pytest.mark.asyncio
async def test_approve_command_no_permission(mock_message, mocker, fake_users):
    group_user = mocker.Mock()
    group_user.telegram_id = 999999  # не в SUPER_USERS_TG_ID
    session = mocker.Mock()
    state = mocker.Mock(spec=FSMContext)

    await approve_commands.approve_command(mock_message, session, state, group_user)
    mock_message.reply.assert_not_awaited()


@pytest.mark.asyncio
async def test_approve_command_no_users(mock_message, mocker):
    group_user = mocker.Mock()
    group_user.telegram_id = SUPER_USERS_TG_ID[0]

    session = mocker.Mock()
    state = mocker.Mock(spec=FSMContext)

    mock_repo = mocker.patch("bot.handlers.approve_handlers.approve_commands.UserRepository")
    mock_repo.return_value.get_not_approved_users = mocker.AsyncMock(return_value=[])

    await approve_commands.approve_command(mock_message, session, state, group_user)

    mock_message.reply.assert_awaited_once_with("Нет пользователей для одобрения.")


@pytest.mark.asyncio
async def test_approve_command_ok(mock_message, mocker, fake_users, mock_create_keyboard):
    group_user = mocker.Mock()
    group_user.telegram_id = SUPER_USERS_TG_ID[0]
    session = mocker.Mock()
    state = mocker.Mock(spec=FSMContext)

    # Патчим UserRepository
    mock_repo = mocker.patch("bot.handlers.approve_handlers.approve_commands.UserRepository")
    repo_instance = mock_repo.return_value
    repo_instance.get_not_approved_users = mocker.AsyncMock(return_value=fake_users)

    mock_create_keyboard.return_value = mocker.Mock()
    mock_message.bot.get_chat_member = mocker.AsyncMock()

    await approve_commands.approve_command(mock_message, session, state, group_user)

    mock_create_keyboard.assert_awaited_once()
    mock_message.reply.assert_called()
    state.set_state.assert_awaited_once_with(approve_commands.ApproveUserStates.started)


@pytest.mark.asyncio
async def test_disapprove_command_no_users(mock_message, mocker):
    group_user = mocker.Mock()
    group_user.user_role = UserRole.ADMIN
    session = mocker.Mock()

    mock_repo = mocker.patch("bot.handlers.approve_handlers.approve_commands.UserRepository")
    mock_repo.return_value.get_approved_users = mocker.AsyncMock(return_value=[])

    await approve_commands.disapprove_command(mock_message, session, group_user)
    mock_message.reply.assert_awaited_once_with("Нет пользователей для отмены регистрации.")


@pytest.mark.asyncio
async def test_delete_command_users_found(mock_message, mocker, fake_users, mock_create_keyboard):
    group_user = mocker.Mock()
    group_user.user_role = UserRole.ADMIN
    session = mocker.Mock()

    mock_repo = mocker.patch("bot.handlers.approve_handlers.approve_commands.UserRepository")
    repo_instance = mock_repo.return_value
    repo_instance.get_not_approved_users = mocker.AsyncMock(return_value=fake_users)

    mock_create_keyboard.return_value = mocker.Mock()
    mock_message.bot.get_chat_member = mocker.AsyncMock()

    await approve_commands.delete_command(mock_message, session, group_user)

    mock_create_keyboard.assert_awaited_once()
    mock_message.reply.assert_called()


@pytest.mark.asyncio
async def test_check_chat_members_skips_invalid(mocker, fake_users: list[dict[str, Any]]):
    """Проверяет пользователей, которые вышли из чата, привязанного к боту"""
    mock_message = mocker.Mock()
    mock_message.bot.get_chat_member = mocker.AsyncMock(side_effect=[None,
                                TelegramBadRequest(method=mock_message,message="не состоит"),
                                TelegramBadRequest(method=mock_message, message="не состоит")])

    user_repo = mocker.Mock()
    user_repo.update_user_by_id = mocker.AsyncMock()

    fake_users[1]["is_approved"] = True
    cleaned = await approve_commands.check_chat_members(user_repo, fake_users, mock_message)

    assert len(cleaned) == 1
    user_repo.update_user_by_id.assert_awaited()
    assert user_repo.update_user_by_id.await_count==2
