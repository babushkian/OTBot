"""Функции для обработки изображений, добавляемых во время регистрации нарушений."""
import hashlib

from io import BytesIO
from pathlib import Path
from dataclasses import dataclass

from PIL import Image
from bot.config import settings
from bot.logger_config import log

@dataclass()
class ImageInfo:
    """Объект, в котором передается информация о сохраненном изображении."""

    hash: str
    path: str
    aspect_ratio: float


def get_hash(image: bytes) -> str:
    """Вычисление контрольной суммы изображения."""
    return hashlib.sha256(image).hexdigest()


def save_image(image: bytes, img_hash: str) -> Path:
    """Сохраняет двоичные данные в файл изображения и возвращает путь к этому файлу."""
    subdir = settings.image_write_dir / img_hash[:2]
    if not subdir.exists():
        subdir.mkdir()
    filename = f"{img_hash}.jpg"
    filepath = subdir / filename
    rel_filepath = settings.image_dir / img_hash[:2] / filename
    if not filepath.exists():
        try:
            with filepath.open("wb") as f:
                f.write(image)
        except Exception as e:
            err_msg = "Ошибка при сохранении изображения в нарушении. %"
            log.error(err_msg % filepath)
            log.exception(e)
            raise Exception(err_msg % filepath)
    return rel_filepath


def get_image_aspect_ratio(image_body: bytes) -> float:
    """Определяет ориентацию изображения для последуюшей компоновки в отчете."""
    image = Image.open(BytesIO(image_body))
    width, height = image.size
    return width / height


def handle_image(image: bytes) ->ImageInfo:
    """Сохраняет двоичные данные в файл и возвращает сведения об этом файле."""
    img_hash = get_hash(image)
    aspect_ratio = get_image_aspect_ratio(image)
    rel_path = save_image(image, img_hash)
    return ImageInfo(hash=img_hash, path=str(rel_path), aspect_ratio=aspect_ratio)


def get_file(path: Path) -> bytes:
    """Возвращает тело файла по его пути."""
    try:
        with path.open("rb") as file:
            return file.read()
    except Exception as e:
        log.error("Не обнаружен файл изображения по адресу %s" % str(path))
        log.exception(e)
        raise e