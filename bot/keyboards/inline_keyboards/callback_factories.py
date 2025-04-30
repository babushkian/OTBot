"""Фабрики для создания callback_data для inline клавиатур."""

from aiogram.filters.callback_data import CallbackData

# TODO REFACTOR разнести фабрики по своим хэндлерам


class ApproveUserFactory(CallbackData, prefix="apuse"):
    """Фабрика для создания callback_data одобрения пользователя."""

    id: int


class DisApproveUserFactory(CallbackData, prefix="disapuse"):
    """Фабрика для создания callback_data отмены регистрации пользователя."""

    id: int


class DeletedUserFactory(CallbackData, prefix="deluse"):
    """Фабрика для создания callback_data удаления пользователя."""

    id: int


class UserRoleFactory(CallbackData, prefix="userrole"):
    """Фабрика для создания callback_data роли пользователя."""

    role: str


class AreaSelectFactory(CallbackData, prefix="areasel"):
    """Фабрика для создания callback_data выбора места нарушения."""

    id: int


class AreaDeleteFactory(CallbackData, prefix="areadel"):
    """Фабрика для создания callback_data выбора места нарушения."""

    id: int


class ResponsibleForAreaFactory(CallbackData, prefix="arearep"):
    """Фабрика для создания callback_data выбора ответственного за место нарушения."""

    id: int
    responsible_name: str


class AreaFieldToUpdateFactory(CallbackData, prefix="arfield"):
    """Фабрика для создания callback_data выбора поля для обновления места нарушения."""

    id: int
    field_name: str
