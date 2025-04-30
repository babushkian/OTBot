"""Обработчики обнаружения нарушений."""
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards.common_keyboards import generate_cancel_button
from bot.handlers.detection_handlers.states import DetectionStates

router = Router(name=__name__)


@router.message(DetectionStates.send_photo)
async def get_violation_photo(message: types.Message,
                              state: FSMContext) -> None:
    """Обрабатывает получение фото нарушения."""
    if not message.photo:
        await message.answer("Необходимо прикрепить фото нарушения.",
                             reply_markup=generate_cancel_button())

    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    description = message.caption or "Без описания"
    picture = await message.bot.download_file(file.file_path)

    await state.update_data(picture=picture.read(), description=description)
    await state.set_state(DetectionStates.enter_area)


@router.message(DetectionStates.enter_area)
async def get_violation_area(message: types.Message,
                             state: FSMContext) -> None:
    """Обрабатывает заполнение места нарушения."""
    # if not message.photo:
    #     await message.answer("Необходимо прикрепить фото нарушения.",
    #                          reply_markup=generate_cancel_button())
    #
    # file_id = message.photo[-1].file_id
    # file = await message.bot.get_file(file_id)
    # description = message.caption or "Без описания"
    # picture = await message.bot.download_file(file.file_path)
    #
    # await state.update_data(picture=picture.read(), description=description)
    #
    # print(await state.get_data())
    #
    # await state.set_state(DetectionStates.enter_area)
