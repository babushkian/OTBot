"""Функции для обработки изображений, добавляемых во время регистрации нарушений."""
import hashlib

from io import BytesIO
from pathlib import Path
from dataclasses import dataclass

from PIL import Image
from bot.config import settings


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
    subdir = settings.image_dir / img_hash[:2]
    if not subdir.exists():
        subdir.mkdir()
    filepath = subdir / f"{img_hash}.jpg"
    if not filepath.exists():
        with filepath.open("wb") as f:
            f.write(image)
    return filepath


def get_image_aspect_ratio(image_body: bytes) -> float:
    """Определяет ориентацию изображения для последуюшей компоновки в отчете."""
    image = Image.open(BytesIO(image_body))
    width, height = image.size
    return width / height


def handle_image(image: bytes) ->ImageInfo:
    """Сохраняет двоичные данные в файл и возвращает сведения об этом файле."""
    img_hash = get_hash(image)
    aspect_ratio = get_image_aspect_ratio(image)
    path = save_image(image, img_hash)
    return ImageInfo(hash=img_hash, path=str(path), aspect_ratio=aspect_ratio)


def get_file(path: Path) -> bytes:
    """Возвращает тело файла по его пути."""
    with path.open("rb") as file:
        return file.read()
