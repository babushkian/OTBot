"""Общие утилиты для бота."""
import re

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


# def dict_to_flat_string(data: dict, separator: str = " ", key_value_separator: str = "=") -> str:
#     """Преобразует словарь в плоскую строку формата key1=value1&key2=value2."""
#     return separator.join(f"{key}{key_value_separator}{value}" for key, value in data.items())
