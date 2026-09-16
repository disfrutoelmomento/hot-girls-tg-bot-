"""Шаблоны текстов сообщений, которые бот шлёт в общий групповой чат."""


def badge_awarded_text(name: str, threshold: int) -> str:
    return f"🔥 {name} держит личный стрик {threshold} дней подряд! Красотка."


def morning_reminder_text(entries: list[tuple[str, list[str]]]) -> str:
    lines = ["Доброе утро! Планы на сегодня:"]
    for name, activities in entries:
        if activities:
            lines.append(f"— {name}: {', '.join(activities)}")
        else:
            lines.append(f"— {name}: план не задан, но фото после тренировки всё равно ждём")
    lines.append("\nПришлите фото в личку боту — оно закроет день.")
    return "\n".join(lines)


def evening_reminder_text(names_not_checked: list[str]) -> str:
    joined = ", ".join(names_not_checked)
    return f"Ещё не отметились сегодня: {joined}. Дедлайн — 23:59, успевайте прислать фото!"


def day_closed_success_text(group_streak: int) -> str:
    return (
        "Все три отметились сегодня! Групповой квест выполнен.\n"
        f"Групповой стрик: {group_streak} дн. подряд."
    )


def day_closed_failed_text(previous_streak: int) -> str:
    if previous_streak > 0:
        return (
            f"Сегодня отметились не все — групповой стрик ({previous_streak} дн.) прервался. "
            "Завтра начинаем заново!"
        )
    return "Сегодня отметились не все — групповой квест не засчитан. Завтра ещё один шанс!"
