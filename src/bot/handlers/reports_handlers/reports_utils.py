"""Утилиты отчётов."""

import re
import json

from pathlib import Path
from datetime import datetime, timezone
from contextlib import suppress

from openpyxl import Workbook

from bot.constants import tz


def remove_default_sheet(wb: Workbook) -> Workbook | None:
    """Удаление листа по умолчанию."""
    with suppress(Exception):
        default_sheet = wb["Sheet"]
        wb.remove(default_sheet)

    return wb


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
