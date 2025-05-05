"""Конфигурация приложения."""
from typing import ClassVar
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки, переменные окружения приложения."""

    BASE_DIR: ClassVar = Path(__file__).parent.parent
    BASE_BOT_DIR: ClassVar = Path(__file__).parent.parent / Path("bot")
    DB_NAME: str
    SUPER_USER_TG_ID: str
    BOT_TOKEN: str

    @property
    def db_url(self) -> str:
        """URL БД приложения."""
        return rf"sqlite+aiosqlite:///{self.BASE_DIR}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / Path(".env"), case_sensitive=False)


# global_commands = ({"command": "start", "description": "Начать работу"},
#                    {"command": "help", "description": "Помощь"})

# Глобальные команды (для всех пользователей)
# GLOBAL_COMMANDS = [
#     BotCommand(command="start", description="Начать работу"),
#     BotCommand(command="help", description="Помощь"),
# ]
#
# # Команды для администраторов
# ADMIN_COMMANDS = [
#                      BotCommand(command="admin", description="Админ-панель"),
#                      BotCommand(command="stats", description="Статистика"),
#                  ] + GLOBAL_COMMANDS

# Команды для обычных пользователей
# USER_COMMANDS = GLOBAL_COMMANDS


settings = Settings()
BASEDIR = settings.BASE_DIR

# if __name__ == "__main__":
#     set_bot_commands()
