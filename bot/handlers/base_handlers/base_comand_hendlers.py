"""Обработчики базовых команд."""
from aiogram import F, Router, types
from openpyxl.reader.excel import load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import UserModel
from logger_config import log
from bot.repositories.user_repo import UserRepository
from bot.handlers.handlers_utils import get_telegram_data
from bot.keyboards.keyboard_utils import create_inline_buttons_from_excel

router = Router(name=__name__)


@router.message(lambda message: message.contact is not None)
async def handle_contact_and_add_user(message: types.Message, session: AsyncSession) -> None:
    """Добавление пользователя в БД."""
    if message.contact:
        user_phone = message.contact.phone_number
        await message.answer(
            f"Спасибо. Вы успешно зарегистрировались с номером {user_phone}. "
            f"Ожидайте одобрения от администратора.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await message.answer("Не удалось получить ваш контакт.")
        return

    user_repo = UserRepository(session)
    user = UserModel(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        phone_number=user_phone,
        telegram_data=await get_telegram_data(message),
    )
    await user_repo.add_user(user)


@router.message(F.document.mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
async def handle_get_xlsx(message: types.Message) -> None:
    """Обработка загружаемых xlsx файлов."""
    file_name = message.document.file_name
    match file_name:
        case "категории нарушений.xlsx":
            # Изменение кнопок категорий нарушений через xlsx файл
            try:
                # получение объекта книги excel
                file_id = message.document.file_id
                bot = message.bot
                file = await bot.get_file(file_id)
                file_data = await bot.download_file(file.file_path)
                excel_workbook = load_workbook(filename=file_data)
                create_inline_buttons_from_excel(excel_workbook=excel_workbook,
                                                 json_file=settings.violation_category_json_file)
            except Exception as e:
                await message.reply(f"Произошла ошибка: {e!r}")
                log.error("Error updating violation categories buttons.")
                log.exception(e)
            else:
                log.success("Categories buttons updated from {file_name}.", file_name=file_name)
                await message.reply("Значения кнопок категорий нарушений обновлены успешно.")
        # TODO case для других сгенерив обработки xlsx файлов 1. # настройка отчётов
        case _:
            msg_text = """При отправке файла xlsx:
             - для обновления категорий нарушений: файл должен иметь имя 'категории нарушений.xlsx'.\n"""
            await message.reply(msg_text)
            return
