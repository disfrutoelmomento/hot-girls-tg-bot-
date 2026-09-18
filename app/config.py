import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name} (см. .env.example)")
    return value


def _parse_whitelist(raw: str) -> dict[int, str]:
    """Формат: "111111111:Аня,222222222:Катя,333333333:Маша" """
    result: dict[int, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        tg_id, name = pair.split(":", 1)
        result[int(tg_id.strip())] = name.strip()
    return result


BOT_TOKEN = _require("BOT_TOKEN")
GROUP_CHAT_ID = int(_require("GROUP_CHAT_ID"))
WHITELIST: dict[int, str] = _parse_whitelist(_require("WHITELIST_USERS"))

TIMEZONE = ZoneInfo("Europe/Moscow")

DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "data" / "habit.db"))
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")

STREAK_BADGE_THRESHOLDS = [3, 7, 14, 30, 60]

# Имя участницы -> цветовая тема Mini App (см. webapp/style.css). Сравнение
# без учёта регистра, чтобы работали и кириллица, и латиница на случай смены
# написания имени в WHITELIST_USERS.
THEME_BY_NAME = {
    "алтана": "altana",
    "altana": "altana",
    "эля": "elya",
    "elya": "elya",
    "маша": "masha",
    "masha": "masha",
}
DEFAULT_THEME = "altana"


def theme_for_name(name: str) -> str:
    return THEME_BY_NAME.get(name.strip().lower(), DEFAULT_THEME)

MORNING_REMINDER_HOUR = int(os.environ.get("MORNING_REMINDER_HOUR", 9))
EVENING_REMINDER_HOUR = int(os.environ.get("EVENING_REMINDER_HOUR", 21))
DAY_CLOSE_HOUR = 23
DAY_CLOSE_MINUTE = 59

WEEKDAY_NAMES_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
# Mini App теперь на английском (бот в чате остаётся на русском), поэтому для
# /api/dashboard нужны свои подписи дней недели.
WEEKDAY_NAMES_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAY_SHORT_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Папка для мотивационных картинок, которые бот иногда шлёт в группу при
# закрытии удачного дня. Пусто по умолчанию — просто положи туда файлы
# (jpg/png), код трогать не нужно, см. app/notify.py.
ASSETS_DIR = BASE_DIR / "assets"
MOTIVATION_IMAGES_DIR = ASSETS_DIR / "motivation"
