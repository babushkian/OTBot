"""Настройки логера loguru."""

from pathlib import Path

from loguru import logger

from bot.config import settings

console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
    "<level>{exception}</level>"
)

LOG_DIR = settings.BASE_DIR / "logs"
if not Path.exists(LOG_DIR):
    Path.mkdir(LOG_DIR, parents=True)

logger.remove()  # Удаляем стандартный обработчик (иначе будет дублирование)

# Вывод логов в консоль
logger.add(
    sink=lambda msg: print(msg, end=""),  # noqa T201
    level="DEBUG",
    colorize=True,
    format=console_format,
)

# Вывод логов в JSON-файл с ротацией и сжатием
JSON_LOG_FILE = LOG_DIR / "log.json"

logger.add(
    JSON_LOG_FILE,
    rotation="10 MB",  # Ротация по размеру файла
    compression="zip",  # Сжатие старых логов
    level="DEBUG",  # Уровень логирования
    serialize=True,  # Логи в формате JSON
    enqueue=True,  # Асинхронная запись
)

log = logger
