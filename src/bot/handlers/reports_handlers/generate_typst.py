from dataclasses import dataclass
import json

from pathlib import Path
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

from bot.db.models import FileModel
from bot.config import settings
from bot.constants import tz, FIT_IMAGES_ASPECT_RATIO
from bot.db.models import UserModel


@dataclass
class ViolationData:
    number: str
    date: str
    photos: str
    description: str
    terms: str
    status: str


def _get_sign_path(user: UserModel) -> Path | None:
    """Если изображение подписи для данного пользователя доступно, возвращает путь, доступный для использования
    в typst-отчете."""
    sign_subpath = Path("signs") / f"{user.id}.png"
    rel_sign_path = settings.image_dir / sign_subpath
    sign_path = settings.image_write_dir / sign_subpath
    if sign_path.exists():
        return Path("..") / rel_sign_path
    return None


def _get_image_path(image: FileModel) -> Path:
    """Возвращает путь фоторгафии из базы, доступняй для использования в typst-шаблоне."""
    return Path("..") / image.path


def _image_string(image: FileModel) -> str:
    """Возвращает фрагмент форматирования typst, представляющий собой картинку."""
    image_path_relative = _get_image_path(image)
    return f'box(inset:0pt, stroke:white)[#image("{image_path_relative}")]'


def _image_grid(images: list[FileModel]) -> str:
    """ "Функция создает фрагмент форматирования, где две фотографии расположены в ряд."""
    output = []
    data_list = []
    template = "grid(columns: ({0}fr, {1}fr), gutter: 2pt,{2})\n"
    for image in images:
        output.append(_image_string(image))
        data_list.append(int(image.aspect_ratio * 100))
    data_list.append(",\n".join(output))
    return template.format(*data_list)


def _image_row_expression(images: list[FileModel]) -> str:
    """Выбирает какой фрагмент форматирования вернуть: одну или две фотографии в ряд."""
    if len(images) == 1:
        return _image_string(images[0])
    elif len(images) > 1:
        return _image_grid(images)
    raise Exception("Пустой список изображений")


def _get_images_layout(images: list[FileModel]) -> str:
    """Компонует фотографии в таблице.

    Если фотографии вертикальные, компонует их по две в ряд. Если горизонтальные, то по одной.
    Возвращает фрагмент форматирования для ячейки таблицы, где размещены все фотографии."""
    imgs_string = ""
    imgs = images.copy()
    imgs.sort(key=lambda x: x.aspect_ratio)
    while imgs:
        pair_aspect_ratio = []
        cur_img = imgs.pop()
        row = [cur_img]
        for pair in imgs:
            pair_aspect_ratio.append(FIT_IMAGES_ASPECT_RATIO - cur_img.aspect_ratio - pair.aspect_ratio)
        only_pozitive_delta = list(filter(lambda x: x >= 0, pair_aspect_ratio))
        if only_pozitive_delta and imgs:
            pair_index = pair_aspect_ratio.index(min(only_pozitive_delta))
            row.append(imgs.pop(pair_index))
        imgs_string += _image_row_expression(row) + ",\n"
    result = "#stack(dir: ttb, {})".format(imgs_string)
    return result


def generate_typst(violations: tuple, created_by: UserModel) -> str:
    """Генерация typst-кода.."""
    responsible_mans = []
    for i in violations:
        if i.area.responsible_user:
            responsible_mans.append(i.area.responsible_user.first_name)
        else:
            responsible_mans.append(i.area.responsible_text)
    responsible_str = ", ".join(set(responsible_mans))
    with settings.report_config_file.open(encoding="utf-8") as file:
        report_settings = json.load(file)

    env = Environment(loader=FileSystemLoader(settings.report_template))
    template = env.get_template("main.j2")
    violation_table = []
    for violation in violations:
        description = f"""
            Описание: {violation.description} \\ \\
            Категория: {violation.category} \\ \\
            Место нарушения: {violation.area.name} \\ \\
            Ответственный: {violation.area.responsible_text} \\ \\
            Нарушение зафиксировал: {violation.detector.first_name}"""

        violation_table.append(
            ViolationData(
                number=violation.number,
                date=violation.created_at.replace(tzinfo=timezone.utc).astimezone(tz=tz).strftime("%d.%m.%Y %H:%M"),
                photos=_get_images_layout(violation.files),
                description=description,
                terms=violation.actions_needed,
                status=violation.status,
            )
        )

    # TODO: вместо словаря лучше передавать объект со всеми параметрами.
    context = {
        "report_settings": report_settings,
        "responsible_str": responsible_str,
        "created_by": created_by,
        "today": datetime.now(tz=tz).strftime("%d.%m.%Y"),
        "violations": violation_table,
        "sign_path": _get_sign_path(created_by),
    }
    typst_code = template.render(**context)
    return typst_code
