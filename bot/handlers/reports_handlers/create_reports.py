"""Создание отчётов нарушений."""
import io
import time
import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from PIL import Image as PILImage
from openpyxl import Workbook
from openpyxl.styles import Side, Border, Alignment
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from openpyxl.drawing.image import Image as OpenpyxlImage
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont

from bot.config import BASEDIR, REPORTS_DIR


def create_pdf(violation: dict, image_scale: float = 1.0) -> bytes:
    """Создание и сохранение pdf отчёта одного нарушения."""
    packet = io.BytesIO()
    pdf = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    font_path = BASEDIR / "bot" / "fonts" / "DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    pdf.setFont("DejaVuSans", 16)

    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(50, height - 50, f"Нарушение номер {violation['id']}")
    pdf.drawString(50, height - 70, f"Место обнаружения: {violation['area']['name']}")

    # ответственный
    responsible = (
        violation["area"]["responsible_text"]
        if not violation["area"]["responsible_user"]
        else violation["area"]["responsible_user"].get("first_name", "")
    )
    pdf.drawString(50, height - 90, f"Ответственный: {responsible}")
    pdf.drawString(50, height - 110, f"Описание: {violation['description']}")

    # изображение
    if violation["picture"]:
        image_stream = io.BytesIO(violation["picture"])
        pil_image = PILImage.open(image_stream)

        # масштаб
        img_width, img_height = pil_image.size
        scaled_width = img_width * image_scale
        scaled_height = img_height * image_scale

        image_buffer = io.BytesIO()
        pil_image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)

        image_reader = ImageReader(image_buffer)

        pdf.drawImage(image_reader, 50, height - 130 - scaled_height, width=scaled_width, height=scaled_height)

    # мероприятия
    actions = violation["actions_needed"]
    pdf.drawString(50, height - 150 - scaled_height, f"Мероприятия: {actions}")
    # создано
    created_by = f"{violation['created_at']} {violation['detector']['first_name']} {violation['detector']['user_role']}"
    pdf.drawString(50, height - 150 - scaled_height - 20, f"Создано: {created_by}")
    pdf.drawString(50, height - 150 - scaled_height - 20, f"Создано: {created_by}")

    pdf.save()
    packet.seek(0)
    violation_report = packet.getvalue()

    # копия на диск
    filename: Path = REPORTS_DIR / f"report_{violation['id']}.pdf"
    with filename.open("wb") as pdf_file:
        pdf_file.write(violation_report)

    return violation_report


def create_xlsx(violations: tuple, image_scale: float = 0.3) -> bytes | None:
    """Отчёт предписания нарушений в формате XLSX."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Предписание"
    violation_numbers = " ,".join([str(violation["id"]) for violation in violations])
    row = 1
    # заголовок
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = f"Предписание нарушений №{violation_numbers}"
    row += 1

    # дата создания предписания
    local_tz = datetime.timezone(datetime.timedelta(hours=-time.timezone / 3600))

    ws.append(["", "Дата предписания:", datetime.datetime.now(tz=local_tz).strftime("%d.%m.%Y")])
    row += 1

    # пустая строка
    ws.append([])
    row += 1
    last_header_row = row

    # шапка таблицы
    headers = [
        "№ нарушения",
        "Дата/время",
        "Фото",
        "Выявленные нарушения требований охраны труда",
        "Сроки устранения, мероприятия",
        "Отметка об устранении",
    ]
    ws.append(headers)

    # заполняем таблицу
    for violation in violations:
        row += 1
        # номер нарушения
        ws[f"A{row}"] = violation["id"]
        ws.column_dimensions["A"].width = 10

        # дата/время
        ws[f"B{row}"] = violation["created_at"].strftime("%d.%m.%Y %H:%M:%S")
        ws.column_dimensions["B"].width = 20

        # фото
        image_stream = io.BytesIO(violation["picture"])
        pil_image = PILImage.open(image_stream)

        original_width, original_height = pil_image.size
        scaled_width = int(original_width * image_scale)
        scaled_height = int(original_height * image_scale)
        pil_image = pil_image.resize((scaled_width, scaled_height))

        temp_image_stream = io.BytesIO()
        pil_image.save(temp_image_stream, format="JPEG")
        temp_image_stream.seek(0)

        img = OpenpyxlImage(temp_image_stream)
        img.anchor = f"C{row}"
        ws.add_image(img)

        padding = 10
        ws.row_dimensions[row].height = scaled_height + padding
        ws.column_dimensions["C"].width = scaled_width / 7 + padding / 7

        # основное содержимое нарушения
        responsible = (  # Ответственный
            violation["area"]["responsible_text"]
            if not violation["area"]["responsible_user"]
            else violation["area"]["responsible_user"].get("first_name", "")
        )
        main_content = (f"Описание нарушения:\n "
                        f"{violation.get('description', 'Без описания.')}\n\n"
                        f"Нарушение категории:\n "
                        f"{violation['category']}\n\n"
                        f"Место нарушения:\n"
                        f"{violation['area']['name']}\n"
                        f"Ответственный:\n"
                        f"{responsible}\n\n"
                        f"Нарушение зафиксировал:\n"
                        f"{violation["detector"]["user_role"]} {violation["detector"]["first_name"]}")
        ws[f"D{row}"] = main_content
        ws.column_dimensions["D"].width = 40

        # мероприятия
        ws[f"E{row}"] = violation["actions_needed"]
        ws.column_dimensions["E"].width = 30
        ws.column_dimensions["F"].width = 20

        # форматирование таблицы
        for table_row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in table_row:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrapText=True)
                if cell.row > last_header_row:
                    cell.border = Border(left=Side(style="thin"),
                                         right=Side(style="thin"),
                                         top=Side(style="thin"),
                                         bottom=Side(style="thin"))

    if len(violations) == 1:
        # отчёт об одном нарушении
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        result = output.getvalue()

        # Копия на диск
        filename: Path = REPORTS_DIR / f"report_{violations[0]['id']}.xlsx"
        with filename.open("wb") as pdf_file:
            pdf_file.write(result)

        return result
