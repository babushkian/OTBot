"""Исключения приложения."""


class EmptyDatabaseSessionError(Exception):
    """Исключение, при отсутствии сессии подключения к БД."""
