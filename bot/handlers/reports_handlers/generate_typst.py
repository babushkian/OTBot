import json

from pathlib import Path
from datetime import datetime, timezone
from bot.db.models import FileModel

from bot.enums import ViolationStatus
from bot.config import BASEDIR
from bot.constants import REPORT_JSON_FILE, tz, FIT_IMAGES_ASPECT_RATIO
from bot.db.models import UserModel

def _get_image_path(image: FileModel) -> Path:
    return Path("..") /  image.path

def _image_string(image: FileModel) -> str:
    image_path_relative = _get_image_path(image)
    return f'image("{image_path_relative}")\n'


def _image_grid(images: list[FileModel]) -> str:
    output = []
    data_list = []
    template = "#grid(columns: ({0}fr, {1}fr), gutter: 2pt,{2})\n"
    for image in images:

        image_path_relative = _get_image_path(image)
        output.append(f'image("{image_path_relative}")')
        data_list.append(int(image.aspect_ratio * 100))
    data_list.append(",\n".join(output))
    return template.format(*data_list)


def _image_row_expression(images: list[FileModel]) -> str:
    if len(images)== 1:
        return f"#{_image_string(images[0])}"
    elif len(images)> 1:
        return _image_grid(images)
    raise Exception("Пустой список изображений")


def _get_images_layout(images: list[FileModel]) -> str:
    imgs_string = ""
    imgs = images.copy()
    imgs.sort(key= lambda x: x.aspect_ratio)
    while imgs:
        pair_aspect_ratio = []
        cur_img = imgs.pop()
        row = [cur_img]
        for pair in imgs:
            pair_aspect_ratio.append(FIT_IMAGES_ASPECT_RATIO - cur_img.aspect_ratio - pair.aspect_ratio)
        only_pozitive_delta = list(filter(lambda x: x>=0, pair_aspect_ratio))
        if only_pozitive_delta and imgs:
            pair_index = pair_aspect_ratio.index(min(only_pozitive_delta))
            row.append(imgs.pop(pair_index))
        imgs_string += _image_row_expression(row)
    #result = "#block(breakable: true, spacing: 0.5pt, fill: lime, stroke: purple)[{}]".format(imgs_string)
    result = "#grid(columns: (1fr,))[{}]".format(imgs_string)
    return result


def generate_typst(violations: tuple, created_by: UserModel) -> str:
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
        images_cell = _get_images_layout(violation.files)

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
            [{images_cell}],
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
