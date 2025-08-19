import pytest
import pytest_asyncio
from bot.handlers.area_handlers import area_commands
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.enums import UserRole
from bot.config import settings
# проверка area_updating
# проверка на то, что пользователь не является суперюзером или админом
# получить список зон для правонарушений
# проверить правильная ли клавиатура получается

@pytest.fixture
def mock_message(mocker):
    message = mocker.Mock(spec=Message)
    message.reply = mocker.AsyncMock()
    message.from_user = mocker.Mock()
    message.from_user.id = settings.SUPER_USERS_TG_ID[0]
    return message


@pytest.fixture
def mock_area_repo(mocker):
    mock_repo = mocker.patch("bot.handlers.area_handlers.area_commands.AreaRepository")
    repo_instance = mock_repo.return_value
    # repo_instance.get_all_areas = mocker.AsyncMock(return_value=[{"id":1, "name":"asda"}, {"id":2, "name":"biaf"},])
    repo_instance.get_all_areas = mocker.AsyncMock(return_value=None)
    return repo_instance


@pytest.fixture
def mock_create_keyboard(mocker):
    mock1 =  mocker.patch(
        "bot.handlers.area_handlers.area_commands.create_keyboard",
        new_callable=mocker.AsyncMock
    )
    mock1.return_value = "some_markup"
    return mock1

@pytest.mark.asyncio
async def test_area_updating_no_permission(mocker, mock_message):
    group_user = mocker.Mock()
    session = mocker.Mock()
    state = mocker.Mock(spec=FSMContext)
    mock_message.from_user = mocker.Mock()
    mock_message.from_user.id = 999999
    await area_commands.area_updating(mock_message, session, state, group_user)
    mock_message.reply.assert_not_awaited()

@pytest.mark.asyncio
async def test_area_updating_role_admin(mocker, mock_message, mock_area_repo, mock_create_keyboard):
    group_user = mocker.Mock()
    group_user.user_role=UserRole.ADMIN
    session = mocker.Mock()
    state = mocker.Mock(spec=FSMContext)
    state.set_state = mocker.AsyncMock()


    await area_commands.area_updating(mock_message, session, state, group_user)
    mock_area_repo.get_all_areas.assert_awaited_once()
    mock_create_keyboard.assert_awaited_once()
    mock_message.reply.assert_awaited()
    state.set_state.assert_awaited_once()
