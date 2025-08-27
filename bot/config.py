"""Конфигурация приложения."""
from typing import ClassVar, Tuple
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    """Настройки, переменные окружения приложения."""

    BASE_DIR: ClassVar = Path(__file__).parent.parent
    BASE_BOT_DIR: ClassVar = Path(__file__).parent.parent / Path("bot")
    DB_NAME: str
    BOT_TOKEN: str
    SUPER_USERS_TG_ID: Tuple[int, ...]
    TG_GROUP_ID: int


    @field_validator("SUPER_USERS_TG_ID", mode="before")
    def parse_tuple(cls, value):
        if isinstance(value, list):
            return tuple(value)
        return (value,)


    @property
    def db_url(self) -> str:
        """URL БД приложения."""
        return rf"sqlite+aiosqlite:///{self.BASE_DIR}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=BASE_DIR / Path(".env"), case_sensitive=False)


settings = Settings()

BASEDIR = settings.BASE_DIR
REPORTS_DIR = BASEDIR / "violations"
IMAGE_DIR = Path("images")
