"""Все тексты, которые бот шлёт в общий групповой чат, собраны здесь.

Как пополнять контент (можно делать в любой момент, отдельно от остального
кода):
- Текст: просто добавляй новые строки в списки *_VARIANTS ниже. Бот каждый
  раз выбирает случайный вариант, так что чем длиннее список — тем меньше
  повторов. Можно довести каждый список хоть до 20-30 штук.
- Стикеры: любая из участниц просто шлёт боту стикер в личку — он сам
  сохранится в общую копилку (БД) и дальше будет случайно выпадать в
  поздравлениях. Ничего в этом файле для этого трогать не нужно
  (см. app/handlers/sticker.py и app/notify.py).
- Картинки: просто положи файлы (jpg/png) в папку assets/motivation/ —
  бот сам начнёт подмешивать их при удачном закрытии дня, ничего в коде
  менять не нужно (см. app/notify.py).
"""

import random

BADGE_VARIANTS = [
    "🔥 {name} держит личный стрик {threshold} дней подряд! Красотка.",
    "🏆 {threshold} дней без пропуска у {name} — это уже привычка!",
    "{name}, ты держишь стрик {threshold} дней подряд! Продолжай в том же духе 💪",
    "Вот это дисциплина — {threshold} дней у {name} без единого пропуска!",
    "{name} прокачала стрик до {threshold} дней. Уважение.",
]

MORNING_GREETINGS = [
    "Доброе утро! Планы на сегодня:",
    "Подъём, красотки! Вот что у нас на сегодня:",
    "Утро! Чем сегодня балуем тело:",
    "Новый день — новый повод собой погордиться. Планы на сегодня:",
    "Доброе утро! Сегодня в программе:",
]

MORNING_CLOSERS = [
    "Пришлите фото в личку боту — оно закроет день.",
    "Как потренируетесь — фото боту в личку, и день в кармане.",
    "Не забудьте прислать фото после тренировки!",
    "Ждём фото в личке — это всё, что нужно для стрика.",
]

EVENING_REMINDER_VARIANTS = [
    "Ещё не отметились сегодня: {names}. Дедлайн — 23:59, успевайте прислать фото!",
    "Время поджимает! {names} — пришлите фото до полуночи, а то стрик под угрозой.",
    "Напоминание: {names} ещё не закрыли день. Время есть до 23:59!",
    "{names}, вы ещё тут? День закрывается в 23:59 — не забудьте фото.",
]

DAY_SUCCESS_VARIANTS = [
    "Все три отметились сегодня! Групповой квест выполнен.\nГрупповой стрик: {streak} дн. подряд.",
    "Идеальный день — все на месте! Групповой стрик: {streak} дн. подряд.",
    "Втроём — значит вместе. Квест дня закрыт! Групповой стрик: {streak} дн.",
    "Три из трёх! Групповой стрик уже {streak} дн. подряд.",
]

DAY_FAILED_WITH_STREAK_VARIANTS = [
    "Сегодня отметились не все — групповой стрик ({streak} дн.) прервался. Завтра начинаем заново!",
    "Увы, не все успели сегодня — стрик в {streak} дн. сгорел. Но завтра новый шанс!",
    "Групповой стрик ({streak} дн.) сегодня прервался. Ничего, завтра наверстаем.",
]

DAY_FAILED_NO_STREAK_VARIANTS = [
    "Сегодня отметились не все — групповой квест не засчитан. Завтра ещё один шанс!",
    "Не в этот раз — но завтра всё получится!",
    "Квест дня не закрыт. Завтра начинаем заново!",
]

def badge_awarded_text(name: str, threshold: int) -> str:
    return random.choice(BADGE_VARIANTS).format(name=name, threshold=threshold)


def morning_reminder_text(entries: list[tuple[str, list[str]]]) -> str:
    lines = [random.choice(MORNING_GREETINGS)]
    for name, activities in entries:
        if activities:
            lines.append(f"— {name}: {', '.join(activities)}")
        else:
            lines.append(f"— {name}: план не задан, но фото после тренировки всё равно ждём")
    lines.append("")
    lines.append(random.choice(MORNING_CLOSERS))
    return "\n".join(lines)


def evening_reminder_text(names_not_checked: list[str]) -> str:
    names = ", ".join(names_not_checked)
    return random.choice(EVENING_REMINDER_VARIANTS).format(names=names)


def day_closed_success_text(group_streak: int) -> str:
    return random.choice(DAY_SUCCESS_VARIANTS).format(streak=group_streak)


def day_closed_failed_text(previous_streak: int) -> str:
    if previous_streak > 0:
        return random.choice(DAY_FAILED_WITH_STREAK_VARIANTS).format(streak=previous_streak)
    return random.choice(DAY_FAILED_NO_STREAK_VARIANTS)
