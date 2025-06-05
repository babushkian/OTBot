"""Создание отчётов нарушений."""
import io
import platform
import subprocess

from pathlib import Path
from collections import defaultdict

from openpyxl import Workbook

from bot.enums import ViolationStatus
from bot.config import BASEDIR
from bot.db.models import UserModel
from logger_config import log
from bot.handlers.reports_handlers.reports_utils import (
    generate_typst,
    remove_default_sheet,
)


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

        cmd = [typst_command, "compile", report_typ_file, output_pdf]

    else:
        cmd = ["typst", "compile", report_typ_file, output_pdf]

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
    # TODO добавить период выгрузки для violations после получения достаточного объема данных
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
    # TODO tests использовать для дальнейшего добавления видов отчётов
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
