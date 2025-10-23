"""Точка вхожа в приложение."""
import asyncio
import contextlib

from asyncio.exceptions import CancelledError

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramForbiddenError
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode


from bot.handlers import router as main_router
from bot.config import settings
from bot.logger_config import log
from bot.set_bot_commands import check_main_menu_on_startup

print(settings.BOT_TOKEN)
print(settings.DB_NAME)
print(settings.DATA_DIR)
print(settings.BASE_DIR)

async def on_startup(bot: Bot) -> None:  # функция выполняется при запуске бота
    """Функция на выполнение при запуске бота."""
    await check_main_menu_on_startup(bot)
    for chat in settings.SUPER_USERS_TG_ID:
        with contextlib.suppress(TelegramForbiddenError):
            await bot.send_message(chat_id=chat, text="Бот вышел online.")
    log.info("Бот запушен.")


async def on_shutdown(bot: Bot) -> None:
    """Функция на выполнение при отключении бота."""
    for chat in settings.SUPER_USERS_TG_ID:
        with contextlib.suppress(TelegramForbiddenError):
            await bot.send_message(chat_id=chat, text="Бот offline.")
    log.info("Бот выключен.")


async def main() -> None:
    """Точка входа."""
    bot = Bot(token=settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML),
              )
    try:
        dp = Dispatcher()
        dp.include_router(main_router)
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except (KeyboardInterrupt, CancelledError):
        log.debug("Бот остановлен принудительной командой.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


# TODO отправка нескольких фото?
# TODO ПЕРЕНАСТРОИТЬ .env  SUPER_USERS_TG в constants
