"""Три ежедневные джобы по Europe/Moscow: утреннее и вечернее напоминание
в группу, и закрытие дня в 23:59 (подведение итога группового квеста).

Планировщик работает в том же asyncio-процессе, что и бот и API — отдельного
воркера/сервиса для него не нужно.
"""

import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import (
    DAY_CLOSE_HOUR,
    DAY_CLOSE_MINUTE,
    EVENING_REMINDER_HOUR,
    MORNING_REMINDER_HOUR,
    TIMEZONE,
    WHITELIST,
)
from app.database import SessionLocal
from app.models import Checkin, DayResult, User, WeeklyPlan
from app.notify import (
    forward_photos_to_group,
    send_celebration_extras,
    send_random_sticker,
    send_to_group,
)
from app.streaks import group_streak, today_msk
from app.texts import (
    day_closed_failed_text,
    day_closed_success_text,
    evening_reminder_text,
    morning_reminder_text,
)

logger = logging.getLogger(__name__)


async def send_morning_reminder() -> None:
    today = today_msk()
    weekday = today.weekday()  # 0=Понедельник ... 6=Воскресенье, совпадает с day_of_week в БД

    entries: list[tuple[str, list[str]]] = []
    with SessionLocal() as db:
        for tg_id, name in WHITELIST.items():
            user = db.query(User).filter(User.telegram_id == tg_id).first()
            activities: list[str] = []
            if user is not None:
                items = (
                    db.query(WeeklyPlan)
                    .filter(WeeklyPlan.user_id == user.id, WeeklyPlan.day_of_week == weekday)
                    .order_by(WeeklyPlan.sort_order)
                    .all()
                )
                activities = [item.activity_label for item in items]
            entries.append((name, activities))

    await send_to_group(morning_reminder_text(entries))
    await send_random_sticker()


async def send_evening_reminder() -> None:
    today_str = today_msk().isoformat()

    with SessionLocal() as db:
        checked_user_ids = {
            row[0]
            for row in db.query(Checkin.user_id).filter(Checkin.checkin_date == today_str).all()
        }
        not_checked = [
            name
            for tg_id, name in WHITELIST.items()
            if not _is_checked(db, tg_id, checked_user_ids)
        ]

    if not not_checked:
        return  # все уже отметились — не дёргаем зря

    await send_to_group(evening_reminder_text(not_checked))


def _is_checked(db, tg_id: int, checked_user_ids: set[int]) -> bool:
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    return bool(user and user.id in checked_user_ids)


async def close_day() -> None:
    """Идемпотентно: если для сегодняшней даты уже есть запись в
    day_results, ничего не делает — это защищает от повторной отправки
    итоговых сообщений, если бот перезапустится рядом с 23:59."""
    today = today_msk()
    today_str = today.isoformat()

    with SessionLocal() as db:
        if db.query(DayResult).filter(DayResult.date == today_str).first() is not None:
            return

        previous_streak = group_streak(db, as_of=today - timedelta(days=1))

        checkins_today = db.query(Checkin).filter(Checkin.checkin_date == today_str).all()
        checked_user_ids = {c.user_id for c in checkins_today}
        all_completed = len(checked_user_ids) >= len(WHITELIST)

        db.add(DayResult(date=today_str, all_completed=all_completed))
        db.commit()

        streak_after = None
        photos_with_captions: list[tuple[str, str | None]] = []
        if all_completed:
            streak_after = group_streak(db, as_of=today)
            id_to_name: dict[int, str] = {}
            for tg_id, name in WHITELIST.items():
                user = db.query(User).filter(User.telegram_id == tg_id).first()
                if user is not None:
                    id_to_name[user.id] = name
            photos_with_captions = [
                (c.photo_file_id, id_to_name.get(c.user_id)) for c in checkins_today
            ]

    if all_completed:
        await send_to_group(day_closed_success_text(streak_after))
        await forward_photos_to_group(photos_with_captions)
        await send_celebration_extras()
    else:
        await send_to_group(day_closed_failed_text(previous_streak))


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_morning_reminder,
        CronTrigger(hour=MORNING_REMINDER_HOUR, minute=0, timezone=TIMEZONE),
        id="morning_reminder",
    )
    scheduler.add_job(
        send_evening_reminder,
        CronTrigger(hour=EVENING_REMINDER_HOUR, minute=0, timezone=TIMEZONE),
        id="evening_reminder",
    )
    scheduler.add_job(
        close_day,
        CronTrigger(hour=DAY_CLOSE_HOUR, minute=DAY_CLOSE_MINUTE, timezone=TIMEZONE),
        id="close_day",
    )
    return scheduler
