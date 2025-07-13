import pytest

from pytest_mock import MockType, MockerFixture
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from bot.enums import UserRole
from bot.constants import SUPER_USERS_TG_ID
from bot.handlers.approve_handlers import approve_commands
from bot.db.database import async_session_factory
from bot.repositories.violation_repo import ViolationRepository

@pytest.mark.asyncio
async def test_get_active_violations_id_description():
    repo=None
    async with async_session_factory() as session:
        repo = ViolationRepository(session)
        res = await repo.get_active_violations_id_description()
        assert isinstance(res, tuple)
        assert len(res) > 0
        assert isinstance(res[0], dict)

    assert repo is not None
