"""Константы бота."""
import time

# команды меню пользователей
common_commands_list = (
    ("start", "Начать работу"),
    ("help", "Помощь"),
)
admin_commands_list = (
    ("approve", "Утвердить пользователя"),
    ("disapprove", "Отменить регистрацию"),
    ("delapprove", "Удалить пользователя"),
    ("area", "Добавить/обновить место нарушения"),
    ("delarea", "Удалить место нарушения"),
    ("check", "Проверка нарушения"),
    ("report", "Запрос отчётов"),
)
otpb_commands_list = (
    ("detect", "Зафиксировать нарушение"),
)
bot_kwarg_names = ("command", "description")

common_commands = [dict(zip(bot_kwarg_names, common, strict=False)) for common in common_commands_list]
otpb_commands = ([dict(zip(bot_kwarg_names, otpb, strict=False)) for otpb in otpb_commands_list] + common_commands)
admin_commands = ([dict(zip(bot_kwarg_names, admin, strict=False)) for admin in admin_commands_list] + otpb_commands)

# мероприятия для нарушений
ACTIONS_NEEDED = (
    "Текст мероприятия номер 1",
    "Текст мероприятия номер 2",
    "Текст мероприятия номер 3",
    "Очень длинный текст для мероприятия номер 4",
)

# id группы в телеграмм
TG_GROUP_ID = -4213770859

TG_GROUP_LINK = "free_orders"
# id суперпользователей в телеграмм
SUPER_USERS_TG_ID = (1238658905, 1881884886)
LOCAL_TIMEZONE = -time.timezone / 3600
