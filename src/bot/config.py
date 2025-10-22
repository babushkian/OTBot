"""Конфигурация приложения."""
from typing import ClassVar, Tuple
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field

PROJECT_ROOT =  Path(__file__).resolve().parents[2]




def find_env_file() -> Path | None:
    # 1) Явный override через переменную окружения ENV_FILE
    env_override = os.getenv("ENV_FILE")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p

    # 2) Проектный .env рядом с корнем репозитория
    p = PROJECT_ROOT / ".env"
    if p.exists():
        return p

    # 3) Частый путь внутри контейнера (если вы монтируете в /app)
    p = Path("/app/.env")
    if p.exists():
        return p

    return None

class Settings(BaseSettings):
    """Настройки, переменные окружения приложения."""
    BASE_DIR: ClassVar = PROJECT_ROOT
    DATA_DIR: ClassVar = PROJECT_ROOT / "data"
    BASE_BOT_DIR: ClassVar = PROJECT_ROOT / "src" / "bot"
    DB_NAME: str
    BOT_TOKEN: str
    SUPER_USERS_TG_ID: Tuple[int, ...]
    TG_GROUP_ID: int


    @computed_field
    @property
    def violation_category_json_file(self) -> Path:
        return self.BASE_BOT_DIR / "keyboards" / "category_buttons.json"

    @computed_field
    @property
    def report_config_file(self) -> Path:
        return self.BASE_BOT_DIR / "handlers" / "reports_handlers" / "report_settings.json"


    @computed_field
    @property
    def typst_dir(self) -> Path:
        return self.DATA_DIR / "typst"

    @computed_field
    @property
    def report_typ_file(self) -> Path:
        return self.typst_dir / "report.typ"

    @computed_field
    @property
    def report_pdf_file(self) -> Path:
        return self.typst_dir / "report.pdf"

    @computed_field
    @property
    def report_template(self) -> Path:
        return self.typst_dir / "template"

    @computed_field
    @property
    def image_dir(self) -> Path:
        """Нужно записывать в базу относительный путь, чтобы typst нормально его обрабатывал"""
        return Path("images")

    @computed_field
    @property
    def image_write_dir(self) -> Path:
        """Нужно записывать в базу относительный путь, чтобы typst нормально его обрабатывал"""
        return self.DATA_DIR / "images"


    @field_validator("SUPER_USERS_TG_ID", mode="before")
    def parse_tuple(cls, value):
        """Если передан список супер-юзеров: возвращает кортеж из них.
        Если передан один супер-юзер, оборачивает его в кортеж."""
        if isinstance(value, list):
            return tuple(value)
        return (value,)



    @property
    def db_url(self) -> str:
        """URL БД приложения."""
        return rf"sqlite+aiosqlite:///{self.DATA_DIR}/{self.DB_NAME}"

    model_config = SettingsConfigDict(case_sensitive=False)

env_path = find_env_file()
if env_path:
    # Загружаем .env в os.environ (только для разработки/локали).
    # В проде обычно env_vars уже переданы docker/k8s, и этот блок ничего не найдёт.
    load_dotenv(env_path)
settings = Settings()


