"""Создание отчётов нарушений."""
import io
import datetime

from copy import copy
from typing import TYPE_CHECKING

from openpyxl.worksheet.worksheet import Worksheet

from bot.constants import COPY_TO, LOCAL_TIMEZONE
from bot.bot_exceptions import InvalidReportParameterError
from bot.handlers.reports_handlers.reports_utils import print_formating, remove_default_sheet, copy_sheet_with_images

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

    pdf.setFont("DejaVuSans", 14)
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


def create_xlsx(violations: tuple,
                image_scale: float = 0.3,
                ) -> Worksheet | bytes:
    """Отчёт предписания нарушений в формате XLSX."""
    # report_template = BASEDIR / "bot" / "docs" / "report_template.xlsx" вариант с шаблоном
    # wb = openpyxl.load_workbook(report_template)
    wb = Workbook()
    # удаление листа по умолчанию
    wb = remove_default_sheet(wb)
    violation_numbers = " ,".join([str(violation["id"]) for violation in violations])
    list_title = f"Предписание №{violation_numbers}"
    ws = wb.create_sheet(title=list_title)
    ws.title = list_title

    # ответственному
    row = 1
    ws[f"F{row}"] = "Ответственному:"
    row += 1
    responsible_mans = []
    for violation in violations:
        if violation["area"].get("responsible"):
            responsible_mans.append(violation["area"]["responsible"])
        else:
            responsible_mans.append(violation["area"]["responsible_text"])
    for responsible in set(responsible_mans):
        ws[f"F{row}"] = responsible
        row += 1

    # копия
    for line in COPY_TO:
        ws[f"F{row}"] = line
        row += 1

    # заголовок
    row += 1
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = list_title

    # дата создания предписания
    row += 1
    local_tz = datetime.timezone(datetime.timedelta(hours=LOCAL_TIMEZONE))
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = f"Дата предписания: {datetime.datetime.now(tz=local_tz).strftime("%d.%m.%Y")}"
    row += 1
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "Устранить следующие нарушения:"

    # пропуск строк для дальнейшего заполнения суммарных отчётов
    ws.append([])

    row += 1
    last_header_row = copy(row)
    ws.append([])
    row += 1

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
        violation_date: datetime.datetime = violation["created_at"] + datetime.timedelta(hours=LOCAL_TIMEZONE)
        ws[f"B{row}"] = violation_date.strftime("%d.%m.%Y %H:%M:%S")
        ws.column_dimensions["B"].width = 20

        # фото
        # TODO найти решение для переменного размера фото
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

    # футер с подписями
    row += 2
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = ("О выполнении настоящего предписания прошу сообщить по каждому пункту согласно сроку "
                     "устранения письменно.")

    row += 2
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "Предписание выдал:"

    row += 2
    ws.append([])
    ws.append(["дата:", "", "подпись", "Ф.И.О.", "", "Должность"])

    row += 2
    ws.merge_cells(f"A{row}:F{row}")
    ws[f"A{row}"] = "Контроль устранения нарушений провел:"

    ws.append([])
    ws.append(["дата:", "", "подпись", "Ф.И.О.", "", "Должность"])
    print_formating(ws)

    # отчёт об одном нарушении
    if len(violations) == 1:
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        result = output.getvalue()

        # Копия на диск
        report_file: Path = REPORTS_DIR / f"report_{violations[0]['id']}.xlsx"
        with report_file.open("wb") as xlsx_file:
            xlsx_file.write(result)

        return result

    return ws


def create_report(violations: tuple, image_scale: float = 0.3) -> bytes | None:
    """Создание суммарного отчёта."""
    # TODO найти решение для включения листа с одним нарушением в суммарный отчёт
    if len(violations) == 1:
        raise InvalidReportParameterError

    wb = Workbook()
    wb = remove_default_sheet(wb)

    wb.create_sheet(title="Статистика")

    violation_areas = {violation["area"]["name"] for violation in violations}

    for area in violation_areas:
        area_violations = tuple([violation for violation in violations if violation["area"]["name"] == area])

        if len(area_violations) > 1:
            copy_sheet_with_images(target_wb=wb,
                                   source_ws=create_xlsx(area_violations,
                                                         image_scale),
                                   ws_title=f"{area}"[:30])

    sum_report_file: Path = REPORTS_DIR / "sum_reports" / "sum_report.xlsx"
    wb.save(sum_report_file)
