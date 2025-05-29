"""Константы бота."""
import time

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
    # {"action": "Провести внеплановый инструктаж", "fix_time": "1 день"},
    # {"action": "Оградить опасную зону", "fix_time": "2 дня"},
    # {"action": "Отстранить от работы", "fix_time": "3 дня"},
    # {"action": "Превести в соответствие", "fix_time": "5 дней"},
    # {"action": "Организовать безопасное складирование деталей", "fix_time": "7 дней"},
    # {"action": "Усилить контроль за выполнением работ", "fix_time": "14 дней"},
    # {"action": "Устранить", "fix_time": "Немедленно"},
    {"action": "Провести внеплановый инструктаж", "fix_time": get_fix_date(days=1)},
    {"action": "Оградить опасную зону", "fix_time": get_fix_date(days=2)},
    {"action": "Отстранить от работы", "fix_time": get_fix_date(days=3)},
    {"action": "Превести в соответствие", "fix_time": get_fix_date(days=5)},
    {"action": "Организовать безопасное складирование деталей", "fix_time": get_fix_date(days=7)},
    {"action": "Усилить контроль за выполнением работ", "fix_time": get_fix_date(days=14)},
    {"action": "Устранить", "fix_time": "Немедленно"},

)

# id группы в телеграмм
TG_GROUP_ID = -4213770859

TG_GROUP_LINK = "free_orders"
# id суперпользователей в телеграмм
SUPER_USERS_TG_ID = (1238658905, 1881884886)
LOCAL_TIMEZONE = -time.timezone / 3600
VIOLATION_CATEGORY_JSON_FILE = BASEDIR / "bot" / "keyboards" / "category_buttons.json"

# текстовые поля для отчётов
COPY_TO = ("Копия:", "главному инженеру ЗАО 'ОмЗиТ'", "Новикову А.Н.", "от ООТ,ПБ и ООС")
