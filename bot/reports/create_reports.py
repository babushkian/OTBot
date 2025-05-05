"""Создание отчётов нарушений."""
import io

from PIL import Image as PILImage

# from openpyxl import Workbook
from reportlab.pdfgen import canvas

# from openpyxl.drawing.image import Image as OpenpyxlImage
from reportlab.lib.pagesizes import letter

from bot.config import BASEDIR


def create_pdf(data: dict, image_scale: float = 1.0) -> bytes:
    """Создание pdf отчёта."""
    packet = io.BytesIO()
    pdf = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    # Загрузка шрифта, поддерживающего кириллицу
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.utils import ImageReader  # Для работы с изображениями из байтового потока
    from reportlab.pdfbase.ttfonts import TTFont

    # Укажите путь к файлу шрифта DejaVuSans.ttf
    font_path = BASEDIR / "bot" / "fonts" / "DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    # Устанавливаем шрифт для всего документа
    pdf.setFont("DejaVuSans", 16)

    # Добавляем текст
    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(50, height - 50, f"Нарушение номер {data['id']}")
    pdf.drawString(50, height - 70, f"Место обнаружения: {data['area']['name']}")

    responsible = (
        data["area"]["responsible_text"]
        if not data["area"]["responsible_user"]
        else data["area"]["responsible_user"].get("first_name", "")
    )
    pdf.drawString(50, height - 90, f"Ответственный: {responsible}")
    pdf.drawString(50, height - 110, f"Описание: {data['description']}")

    # Добавляем изображение после описания
    if data["picture"]:
        image_stream = io.BytesIO(data["picture"])
        pil_image = PILImage.open(image_stream)

        # Получаем оригинальные размеры изображения
        img_width, img_height = pil_image.size

        # Масштабируем изображение с учетом коэффициента
        scaled_width = img_width * image_scale
        scaled_height = img_height * image_scale

        # Преобразуем изображение обратно в байты
        image_buffer = io.BytesIO()
        pil_image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)

        # Используем ImageReader для загрузки изображения из байтового потока
        image_reader = ImageReader(image_buffer)

        # Добавляем изображение в PDF
        pdf.drawImage(image_reader, 50, height - 130 - scaled_height, width=scaled_width, height=scaled_height)

    # Добавляем текст created_by после изображения
    actions = data["actions_needed"]
    pdf.drawString(50, height - 150 - scaled_height, f"Мероприятия: {actions}")
    created_by = f"{data['created_at']} {data['detector']['first_name']} {data['detector']['user_role']}"
    pdf.drawString(50, height - 150 - scaled_height - 20, f"Создано: {created_by}")

    # Сохраняем PDF в поток байтов
    pdf.save()
    packet.seek(0)
    return packet.getvalue()


# # Функция для сохранения данных в XLSX
# def create_xlsx(data):
#     # Создаем новую книгу Excel
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "Нарушение"
#
#     # Заполняем данные
#     ws.append(["Нарушение номер", data["id"]])
#     ws.append(["Место обнаружения", data["area"]["name"]])
#     responsible = (
#         data["area"]["responsible_text"]
#         if not data["area"]["responsible_user"]
#         else data["area"]["responsible_user"].get("first_name", "")
#     )
#     ws.append(["Ответственный", responsible])
#     ws.append(["Описание", data["description"]])
#     ws.append(["Создано", f"{data['created_at']} {data['detector']['first_name']} {data['detector']['user_role']}"])
#
#     # Добавляем изображение
#     if data["picture"]:
#         image_stream = io.BytesIO(data["picture"])
#         pil_image = PILImage.open(image_stream)
#         pil_image.save("temp_image.jpg")  # Сохраняем временный файл
#         img = OpenpyxlImage("temp_image.jpg")
#         ws.add_image(img, "A7")  # Размещаем изображение в ячейке A7
#
#     # Сохраняем файл
#     wb.save("violation.xlsx")
