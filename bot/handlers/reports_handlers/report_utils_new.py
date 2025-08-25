import json

from pathlib import Path
from datetime import datetime, timezone


from bot.enums import ViolationStatus
from bot.config import BASEDIR
from bot.constants import REPORT_JSON_FILE, tz
from bot.db.models import UserModel


def generate_typst_new(violations: tuple, created_by: UserModel) -> str:
    """Генерация typst-кода.."""
    output_dir = BASEDIR / Path("typst") / Path("violation_images")

    responsible_mans = []
    for i in violations:
        if i.area.responsible_user:
            responsible_mans.append(i.area.responsible_user.first_name)
        else:
            responsible_mans.append(i.area.responsible_text)

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
    for i, violation in enumerate(violations, start=1):
        # временная копия изображения
        images_string = ""
        for file in violation.files:
            image_path_relative = "..\\" + file.path
            images_string += f'image("{image_path_relative}", width: {report_settings["col_width"]["C"]}),\n'

        # описание нарушения
        description = f"""
            Описание: {violation.description} \\ \\
            Категория: {violation.category} \\ \\
            Место нарушения: {violation.area.name} \\ \\
            Ответственный: {violation.area.responsible_text} \\ \\
            Нарушение зафиксировал: {violation.detector.first_name}"""

        # заполнение таблицы
        # Форматируем дату с учетом временной зоны
        localized_datetime = (violation.created_at.replace(tzinfo=timezone.utc)
                              .astimezone(tz=tz).strftime("%d.%m.%Y %H:%M"))
        typst_code += f"""
            [{violation.id}],
            [{localized_datetime}],
            [#stack({images_string})],
            [#align(left)[{description}]],
            [#align(left)[{violation.actions_needed}]],
            [#text(size: 10pt, weight: "bold")[{violation.status}]],
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
