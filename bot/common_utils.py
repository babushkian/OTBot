"""Общие утилиты для бота."""
import re

from datetime import datetime, timezone, timedelta

from bot.bot_exceptions import StringInputError, EmptyValueInputError


def verify_string_as_filename(input_string: str) -> str:
    """Проверяет строку на возможность использования её в качестве имени файла."""
    if not input_string:
        raise EmptyValueInputError

    invalid_chars = "[\\\\/:*?&quot;|1234567890_&lt&gt]"
    max_length = 255

    if re.search(invalid_chars, input_string):
        raise StringInputError(invalid_chars=invalid_chars)

    if len(input_string) > max_length:
        raise StringInputError(max_length=max_length)

    return input_string


def verify_string_as_integer(input_string: str) -> tuple[bool, str | None]:
    """Проверяет строку на возможность использования её в качестве целого числа."""
    try:
        int(input_string)
    except ValueError:
        return False, "Введите целое число."
    else:
        return True, None


def get_fix_date(days: int, tz: timezone = timezone(timedelta(hours=6))) -> str:
    """Возвращает дату в формате DD.MM.YYYY, устранения нарушения от текущего дня. Проверяет выходные дни."""
    fix_date = datetime.now(tz=tz) + timedelta(days=days)
    while fix_date.weekday() >= 5:
        fix_date += timedelta(days=1)

    return fix_date.strftime("%d.%m.%Y")
