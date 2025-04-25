"""Точка вхожа в приложение."""
import asyncio

from asyncio.exceptions import CancelledError

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from bot.config import settings, set_bot_commands
from bot.handlers import router as main_router
from logger_config import log


async def on_startup(bot: Bot) -> None:  # функция выполняется при запуске бота
    """Функция на выполнение при запуске бота."""
    await bot.send_message(chat_id=settings.SUPER_USER_TG_ID, text="Бот вышел online.")
    log.info("Бот запушен.")


async def on_shutdown(bot: Bot) -> None:
    """Функция на выполнение при отключении бота."""
    await bot.send_message(chat_id=settings.SUPER_USER_TG_ID, text="Бот offline.")
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
        await set_bot_commands(bot)  # установка команд
        # dp.update.middleware(AuthMiddleware())  # добавление middleware
        await dp.start_polling(bot)
    except (KeyboardInterrupt, CancelledError):
        log.debug("Бот остановлен принудительной командой.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
