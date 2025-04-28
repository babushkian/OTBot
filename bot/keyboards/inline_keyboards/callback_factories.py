"""Фабрики для создания callback_data для inline клавиатур."""

from aiogram.filters.callback_data import CallbackData


class ApproveUserFactory(CallbackData, prefix="apuse"):
    """Фабрика для создания callback_data одобрения пользователя."""

    id: int


class DisApproveUserFactory(CallbackData, prefix="disapuse"):
    """Фабрика для создания callback_data одобрения пользователя."""

    id: int


class UserRoleFactory(CallbackData, prefix="userrole"):
    """Фабрика для создания callback_data роли пользователя."""

    role: str
