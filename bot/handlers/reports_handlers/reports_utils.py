"""Утилиты отчётов."""
import re
import json

from pathlib import Path
from datetime import datetime, timezone
from contextlib import suppress

from openpyxl import Workbook

from bot.enums import ViolationStatus
from bot.config import BASEDIR
from bot.constants import REPORT_JSON_FILE, tz
from bot.db.models import UserModel


def remove_default_sheet(wb: Workbook) -> Workbook | None:
    """Удаление листа по умолчанию."""
    with suppress(Exception):
        default_sheet = wb["Sheet"]
        wb.remove(default_sheet)

    return wb


def generate_typst(violation_json_data: tuple, created_by: UserModel) -> str:
    """Генерация typst-кода.."""
    output_dir = BASEDIR / Path("typst") / Path("violation_images")
    # ответственные
    responsible_mans = [line["area"].get("responsible_user")["first_name"] if line["area"].get("responsible_user")
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
        //#set text(font: "Arial", size: 10pt)        
        #set text(
            font: (
                "Liberation Sans",  // Основной шрифт для Linux
                "Noto Sans",        // Fallback 1
                "DejaVu Sans",      // Fallback 2
                "Arial",            // Fallback 3 (если вдруг есть)
            ),
            size: 10pt
            )        
        #set heading(numbering: "1.")

        // стили
        #let centered-title(body) = align(center)[
            #text(size: 16pt, weight: "bold")[#body]]

        // шапка
        #align(right)[Ответственным: \\ {responsible_str}.]
        //#align(right)[Копия: главному инженеру \\ {report_settings["engineer"]}.]
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
        # Форматируем дату с учетом временной зоны
        localized_datetime = (violation["created_at"].replace(tzinfo=timezone.utc)
                              .astimezone(tz=tz).strftime("%d.%m.%Y %H:%M"))
        typst_code += f"""
            [{violation["id"]}],
            [{localized_datetime}],
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
