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


settings = Settings()
BASEDIR = settings.BASE_DIR
REPORTS_DIR = BASEDIR / "violations"
