"""Утилиты при обнаружении нарушения."""

from io import BytesIO
from PIL import Image


async def merge_images(image_bytes_list: list[bytes], gap: int = 10) -> BytesIO:
    """Склеивает 1-4 фото в квадрат 2x2 с зазором между фото."""
    images = [Image.open(BytesIO(img)) for img in image_bytes_list]

    # Если 2 фото — склеиваем горизонтально
    if len(images) == 2:
        total_width = images[0].width + images[1].width + gap  # Ширина с учетом зазора
        max_height = max(img.height for img in images)  # Максимальная высота
        new_img = Image.new("RGB", (total_width, max_height), color=(255, 255, 255))  # Белый фон
        new_img.paste(images[0], (0, 0))  # Первое фото слева
        new_img.paste(images[1], (images[0].width + gap, 0))  # Второе фото справа

    # Если 3-4 фото — склеиваем в сетку 2x2
    else:
        max_width = max(img.width for img in images)  # Максимальная ширина
        max_height = max(img.height for img in images)  # Максимальная высота
        total_width = max_width * 2 + gap  # Ширина с учетом зазора
        total_height = max_height * 2 + gap  # Высота с учетом зазора
        new_img = Image.new("RGB", (total_width, total_height), color=(255, 255, 255))  # Белый фон

        # Размещаем фото с учетом зазоров
        new_img.paste(images[0], (0, 0))  # Лево-верх
        new_img.paste(images[1], (max_width + gap, 0))  # Право-верх
        if len(images) >= 3:
            new_img.paste(images[2], (0, max_height + gap))  # Лево-низ
        if len(images) >= 4:
            new_img.paste(images[3], (max_width + gap, max_height + gap))  # Право-низ

    # Сохраняем результат в BytesIO
    output = BytesIO()
    new_img.save(output, format="JPEG")
    output.seek(0)
    return output
