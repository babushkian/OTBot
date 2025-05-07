"""Утилиты отчётов."""
from copy import copy
from contextlib import suppress

from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.worksheet import Worksheet


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
