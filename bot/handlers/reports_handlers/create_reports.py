"""Создание отчётов нарушений."""
import io
import datetime
import platform
import subprocess

from copy import copy
from pathlib import Path
from collections import defaultdict

from PIL import Image as PILImage
from openpyxl import Workbook
from openpyxl.styles import Side, Border, Alignment
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.worksheet.worksheet import Worksheet

from bot.enums import ViolationStatus
from bot.config import BASEDIR, REPORTS_DIR
from bot.constants import COPY_TO, LOCAL_TIMEZONE
from bot.db.models import UserModel
from logger_config import log
from bot.bot_exceptions import InvalidReportParameterError
from bot.handlers.reports_handlers.reports_utils import (
    generate_typst,
    print_formating,
    remove_default_sheet,
    copy_sheet_with_images,
)

# TODO remove deprecated functions

def create_xlsx(violations: tuple,
                image_scale: float = 0.3,
                ) -> Worksheet | bytes:
    """Отчёт предписания нарушений в формате XLSX."""
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

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def create_typst_report(created_by: UserModel,
                        violations: tuple) -> Path:
    """Создание отчёта pdf с помощью typst."""
    typst_document = generate_typst(violations, created_by=created_by)

    report_typ_file = BASEDIR / Path("typst") / Path("report.typ")
    with report_typ_file.open("w", encoding="utf-8") as typ_file:
        typ_file.write(typst_document)

    output_pdf = BASEDIR / Path("violations") / report_typ_file.with_suffix(".pdf").name

    if platform.system() == "Windows":
        typst_command = (r"C:\Users\user-18\AppData\Local\Microsoft\WinGet\Packages"
                         r"\Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe"
                         r"\typst-x86_64-pc-windows-msvc\typst.exe")
    else:
        typst_command = "typst"

    cmd = [typst_command, "compile", report_typ_file, output_pdf]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    if result.returncode != 0:
        log.error(f"Ошибка компиляции:\n{result.stderr}")
        msg = "Не удалось скомпилировать Typst файл"
        raise RuntimeError(msg)

    log.success(f"PDF успешно создан: {output_pdf}")
    return output_pdf


def create_static_report(violations: tuple) -> bytes:
    """Создание статистического отчёта xlsx."""
    # TODO добавить период выгрузки для violations
    wb = Workbook()
    wb = remove_default_sheet(wb)

    # полный отчёт
    wb.create_sheet(title="Полный отчёт")
    full_report_ws = wb["Полный отчёт"]
    # шапка
    full_report_ws.append([
        "Номер нарушения",  # ["id"]
        "Место нарушения",  # ["area"]["name"]
        "Описание нарушения",  # ["description]
        "Ответственный",  # ["area"]["responsible_user"] if responsible_user_id else ["area"]["responsible_text"]
        "Категория нарушения",  # ["category"]
        "Мероприятия",  # ["actions_needed"]
        "Статус",  # ["status"]
        "Дата обнаружения",  # ["created_at"]
        "Дата закрытия",  # ["updated_at"] if status == <ViolationStatus.COMPLETED: 'завершено'> else ""
        "Обнаружено работником",  # ["detector"]["first_name"] + ["detector"]["user_role"]
    ])
    # данные полного отчёта
    for violation in violations:
        full_report_ws.append([
            violation["id"],
            violation["area"]["name"],
            violation.get("description", ""),
            violation["area"]["responsible_user"]["first_name"] if violation["area"]["responsible_user_id"] else
            violation["area"][
                "responsible_text"],
            violation["category"],
            violation["actions_needed"],
            violation["status"].value,
            violation["created_at"].strftime("%d.%m.%Y %H:%M:%S"),
            violation["updated_at"].strftime("%d.%m.%Y %H:%M:%S") if violation["status"].name == "CORRECTED" else "",
            f"ФИО: {violation["detector"]["first_name"]} Роль:{violation["detector"]["user_role"]}",
        ])

    # отчёт по каждому месту нарушения
    area_report_data = {}
    # TODO tests
    # vis = [{k: v for k, v in violation.items() if k != "picture"} for violation in violations]
    # pprint(vis)

    for violation in violations:
        area_name = violation["area"]["name"]
        responsible = violation["area"]["responsible_user"]["first_name"] if violation["area"]["responsible_user_id"] \
            else violation["area"]["responsible_text"]
        status = violation["status"].value

        if area_name not in area_report_data:
            area_report_data[area_name] = {"violations": defaultdict(int)}

        area_report_data[area_name]["violations"][status] += 1
        area_report_data[area_name]["responsible"] = responsible

    wb.create_sheet(title="Места нарушения")
    area_report_ws = wb["Места нарушения"]

    # шапка
    area_report_ws.append([
        "Место нарушения",
        "Ответственный",
        ViolationStatus.ACTIVE.value,
        ViolationStatus.REVIEW.value,
        ViolationStatus.CORRECTED.value,
        ViolationStatus.REJECTED.value,
    ])
    # данные полного отчёта
    for area, violation_statuses in area_report_data.items():
        area_report_ws.append([
            area,
            violation_statuses["responsible"],
            violation_statuses["violations"].get(ViolationStatus.ACTIVE.value, 0),
            violation_statuses["violations"].get(ViolationStatus.REVIEW.value, 0),
            violation_statuses["violations"].get(ViolationStatus.CORRECTED.value, 0),
            violation_statuses["violations"].get(ViolationStatus.REJECTED.value, 0),
        ])

    # результат
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return output.getvalue()
