"""Утилиты отчётов."""
import re
import json

from copy import copy
from pathlib import Path
from datetime import datetime
from contextlib import suppress

from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.worksheet import Worksheet

from bot.enums import ViolationStatus
from bot.config import BASEDIR
from bot.constants import REPORT_JSON_FILE, tz
from bot.db.models import UserModel

# TODO remove unused and deprecated functions

def print_formating(sh_obj: Worksheet) -> None:
    """Форматирует лист excel для печати."""
    sh_obj.page_setup.orientation = "portrait"
    sh_obj.page_setup.paperSize = sh_obj.PAPERSIZE_A3
    cm = 1.0 / 2.54  # размер полей - перевод в сантиметры из дюймов
    sh_obj.page_margins = PageMargins(left=cm, right=cm, top=int(cm), bottom=int(cm))
    sh_obj.print_options.verticalCentered = True  # вертикальное центрирования
    sh_obj.print_options.horizontalCentered = True  # горизонтальное центрирование
    sh_obj.page_setup.fitToWidth = True


def remove_default_sheet(wb: Workbook) -> Workbook | None:
    """Удаление листа по умолчанию."""
    with suppress(Exception):
        default_sheet = wb["Sheet"]
        wb.remove(default_sheet)

    return wb


def copy_sheet_with_images(source_ws: Worksheet, target_wb: Workbook, ws_title: str) -> Worksheet:
    """Копирует лист excel с изображениями в новую книгу."""
    target_ws = target_wb.create_sheet(title=ws_title)

    for row in source_ws.iter_rows():
        for cell in row:
            target_cell = target_ws[cell.coordinate]
            target_cell.value = cell.value

            # стили
            if cell.has_style:
                target_cell.font = copy(cell.font)
                target_cell.border = copy(cell.border)
                target_cell.fill = copy(cell.fill)
                target_cell.number_format = copy(cell.number_format)
                target_cell.protection = copy(cell.protection)
                target_cell.alignment = copy(cell.alignment)

    # объединённые ячейки
    for merged_range in source_ws.merged_cells.ranges:
        target_ws.merge_cells(str(merged_range))

    # ширина столбцов
    for col in source_ws.column_dimensions:
        target_ws.column_dimensions[col] = copy(source_ws.column_dimensions[col])

    # высота строк
    for row_idx, row_dim in source_ws.row_dimensions.items():
        target_ws.row_dimensions[row_idx] = copy(row_dim)

    # изображения
    for img_obj in source_ws._images:
        # новое изображение на основе исходного
        new_img = OpenpyxlImage(img_obj.ref)
        # координаты изображения
        anchor = img_obj.anchor
        target_ws.add_image(new_img, anchor)

    return target_ws


def generate_typst(violation_json_data: tuple, created_by: UserModel) -> str:
    """Генерация typst-кода.."""
    output_dir = BASEDIR / Path("typst") / Path("violation_images")
    # ответственные
    responsible_mans = [line["area"].get("responsible_user") if line["area"].get("responsible_user")
                        else line["area"]["responsible_text"] for line in
                        violation_json_data]
    responsible_str = ", ".join(set(responsible_mans))
    with REPORT_JSON_FILE.open(encoding="utf-8") as file:
        report_settings = json.load(file)

    typst_code = f"""
        // базовые настройки
        #set page(
                width: {report_settings["page_size"]["width"]},
                height: {report_settings["page_size"]["height"]},
                margin: {report_settings["page_size"]["margin"]}
                )
        #set text(font: "Arial", size: 10pt)
        #set heading(numbering: "1.")

        // стили
        #let centered-title(body) = align(center)[
            #text(size: 16pt, weight: "bold")[#body]]

        // шапка
        #align(right)[Ответственным: \\ {responsible_str}.]
        #align(right)[Копия: главному инженеру \\ {report_settings["engineer"]}.]
        #align(right)[от {created_by.user_role if created_by else "Ведущий инженер по ОТ и ПБ"} \\
        {created_by.first_name if created_by else "Жгулев Н.С./Муталинов Т.Е."}]

        // заголовок
        #centered-title[Предписание]
        Дата формирования предписания: {datetime.now(tz=tz).strftime('%d.%m.%Y')}
        #centered-title[Устранить следующие нарушения:]

        // таблица
        #set table(
            align: center,
            inset: 5pt,
            stroke: 0.5pt
            )
        #table(
            columns: (
                {report_settings["col_width"]["A"]},
                {report_settings["col_width"]["B"]}, 
                {report_settings["col_width"]["C"]},
                {report_settings["col_width"]["D"]},
                {report_settings["col_width"]["E"]},
                {report_settings["col_width"]["F"]},
                    ),
            // шапка таблицы
            [*{report_settings["headers"]["A"]}*],
            [*{report_settings["headers"]["B"]}*],
            [*{report_settings["headers"]["C"]}*],
            [*{report_settings["headers"]["D"]}*],
            [*{report_settings["headers"]["E"]}*],
            [*{report_settings["headers"]["F"]}*],
        """

    # Обработка каждого нарушения
    for i, violation in enumerate(violation_json_data, start=1):
        # временная копия изображения
        image_path = output_dir / f"violation_{i}.jpg"
        with image_path.open("wb") as jpg_file:
            jpg_file.write(violation["picture"])

        image_path_relative = output_dir.relative_to(BASEDIR / Path("typst")) / f"violation_{i}.jpg"
        if violation["status"] == ViolationStatus.ACTIVE.value:
            actual_status = "активно"
        elif violation["status"] == ViolationStatus.CORRECTED.value:
            actual_status = "устранено"
        elif violation["status"] == ViolationStatus.REVIEW.value:
            actual_status = "проверяется"
        else:
            actual_status = "отклонено"

        # описание нарушения
        description = f"""
            Описание: {violation['description']} \\ \\
            Категория: {violation['category']} \\ \\
            Место нарушения: {violation['area']['name']} \\ \\
            Ответственный: {violation['area']['responsible_text']} \\ \\
            Нарушение зафиксировал: {violation['detector']['first_name']}"""

        # заполнение таблицы
        typst_code += f"""
            [{violation["id"]}],
            [{violation['created_at'].strftime('%d.%m.%Y %H:%M')}],
            image("{image_path_relative}", width: {report_settings["col_width"]["C"]}),
            [#align(left)[{description}]],
            [#align(left)[{violation['actions_needed']}]],
            [#text(size: 10pt, weight: "bold")[{actual_status}]],
        """

    # footer
    typst_code += f""")
        \\
        #text(size: 12pt, weight: "bold")[О выполнении настоящего предписания прошу сообщить по
        каждому пункту \\ согласно сроку устранения письменно.]
        \\
        \\
        #align(left)[
        Предписание выдал: \\ \\
        дата:#h(0.5cm) {datetime.now(tz=tz).strftime('%d.%m.%Y')} #h(0.5cm)
        подпись:#h(2cm) {created_by.first_name if created_by else "Жгулев Н.С./Муталинов Т.Е."}
        {created_by.user_role if created_by else "Ведущий инженер по ОТ и ПБ"}
        ]
        \\
        #align(left)[
        Контроль устранения нарушений провел: \\ \\
        дата:#h(3cm)
        подпись:#h(2cm) 
        // {created_by.first_name if created_by else "Жгулев Н.С./Муталинов Т.Е."}
        // {created_by.user_role if created_by else "Ведущий инженер по ОТ и ПБ"}
        ]"""

    return typst_code


def validate_date_interval(date_interval: str) -> bool | tuple[datetime, datetime]:
    """Валидатор для строки с интервалом дат в формате "DD-MM-YYYY DD-MM-YYYY"."""
    pattern = r"^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-(\d{4}) (0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-(\d{4})$"

    if not re.match(pattern, date_interval):
        return False

    start_date_str, end_date_str = date_interval.split()

    try:
        start_date = datetime.strptime(start_date_str, "%d-%m-%Y").astimezone(tz=tz)
        end_date = datetime.strptime(end_date_str, "%d-%m-%Y").astimezone(tz=tz)
        result = (start_date, end_date)
    except ValueError:
        return False

    if end_date < start_date:
        return False

    return result
