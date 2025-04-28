"""Исключения приложения."""


class EmptyDatabaseSessionError(Exception):
    """Исключение, при отсутствии сессии подключения к БД."""


class EmptyValueInputError(ValueError):
    """Исключение для ввода пустого значения."""

    def __init__(self) -> None:
        """Инициализация текста исключения."""
        super().__init__("Значение не может быть пустым.")


class StringInputError(ValueError):
    """Исключение для ввода некорректного значения строки."""

    def __init__(
            self,
            *,
            invalid_chars: str | None = None,
            max_length: int | None = None,
    ) -> None:
        """Инициализация текста исключения."""
        messages = []

        if invalid_chars:
            messages.append(f"Строка содержит недопустимые символы: {invalid_chars}")
        if max_length:
            messages.append(f"Строка слишком длинная. Максимальная длина: {max_length} символов.")

        # Объединяем все сообщения в одну строку
        error_message = "/n".join(messages)
        super().__init__(error_message)
