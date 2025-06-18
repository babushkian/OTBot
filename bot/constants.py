"""Константы бота."""

from pathlib import Path
from datetime import timezone, timedelta

from bot.config import BASEDIR
from bot.common_utils import get_fix_date

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
    ("vclose", "Закрытие нарушений"),
)
otpb_commands_list = (
    ("detect", "Зафиксировать нарушение"),
    ("vclose", "Закрытие нарушений"),
)
bot_kwarg_names = ("command", "description")

common_commands = [dict(zip(bot_kwarg_names, common, strict=False)) for common in common_commands_list]
otpb_commands = ([dict(zip(bot_kwarg_names, otpb, strict=False)) for otpb in otpb_commands_list] + common_commands)
admin_commands = ([dict(zip(bot_kwarg_names, admin, strict=False)) for admin in admin_commands_list] + otpb_commands)
LOCAL_TIMEZONE = 6
tz = timezone(timedelta(hours=LOCAL_TIMEZONE))

# мероприятия для нарушений

def action_needed_deadline():
    return (
        {"action": "Провести внеплановый инструктаж", "fix_time": get_fix_date(days=1, tz=tz)},
        {"action": "Оградить опасную зону", "fix_time": "Немедленно"},
        {"action": "Отстранить от работы", "fix_time": "Немедленно"},
        {"action": "Превести в соответствие", "fix_time": get_fix_date(days=3, tz=tz)},
        {"action": "Организовать безопасное складирование деталей", "fix_time": get_fix_date(days=3, tz=tz)},
        {"action": "Усилить контроль за выполнением работ", "fix_time": "Немедленно"},
        {"action": "Устранить", "fix_time": get_fix_date(days=3, tz=tz)},
    )

# максимальное количество фото
MAX_SEND_PHOTO = 4
# время ожидания в секундах загрузки каждого фото когда пользователь отправляет несколько фото
MAX_SECONDS_TO_WAIT_WHILE_UPLOADING_PHOTOS = 2


# id группы в телеграмм
TG_GROUP_ID = -1002157254601
# id суперпользователей в телеграмм
SUPER_USERS_TG_ID = (1238658905, 1881884886, 177201205)
#SUPER_USERS_TG_ID = (177201205,)

VIOLATION_CATEGORY_JSON_FILE = BASEDIR / Path("bot") / Path("keyboards") / Path("category_buttons.json")
REPORT_JSON_FILE = BASEDIR / Path("bot") / Path("handlers") / Path("reports_handlers") / Path("report_settings.json")
