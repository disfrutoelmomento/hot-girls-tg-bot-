"""Расчёт личного и группового стрика.

Стрики нигде не хранятся отдельным счётчиком — считаем их на лету по датам
в checkins (личный) и day_results (групповой). При 3 пользователях и
горизонте ~90 дней это дёшево, зато исключает рассинхронизацию счётчика
с реальными данными.
"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import TIMEZONE, WHITELIST
from app.models import Checkin, DayResult


def today_msk() -> date:
    return datetime.now(TIMEZONE).date()


def _checkin_dates(db: Session, user_id: int) -> set[str]:
    rows = db.query(Checkin.checkin_date).filter(Checkin.user_id == user_id).all()
    return {r[0] for r in rows}


def personal_streak(db: Session, user_id: int, as_of: date | None = None) -> int:
    """Считаем непрерывную серию дней с отметкой, идя назад от сегодняшнего дня.

    Если сегодня ещё нет отметки, это не обнуляет стрик сразу — день ещё не
    закрыт (дедлайн 23:59), поэтому начинаем считать со вчерашнего дня.
    Если пропущен хотя бы один день — серия обрывается.
    """
    as_of = as_of or today_msk()
    dates = _checkin_dates(db, user_id)

    cursor = as_of
    if cursor.isoformat() not in dates:
        cursor -= timedelta(days=1)

    streak = 0
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def group_streak(db: Session, as_of: date | None = None) -> int:
    """Аналогично personal_streak, но по таблице day_results (all_completed).

    Сегодняшний день ещё может быть не закрыт планировщиком (это происходит
    в 23:59), поэтому если для as_of записи ещё нет — тоже начинаем со
    вчерашнего дня, не обнуляя стрик раньше времени.
    """
    as_of = as_of or today_msk()
    rows = db.query(DayResult.date, DayResult.all_completed).all()
    completed_dates = {r[0] for r in rows if r[1]}
    known_dates = {r[0] for r in rows}

    cursor = as_of
    if cursor.isoformat() not in known_dates:
        cursor -= timedelta(days=1)

    streak = 0
    while cursor.isoformat() in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def today_quest_status(db: Session, on_date: date | None = None) -> dict[int, bool]:
    """Кто из участниц (telegram_id) уже отметился в заданный день."""
    on_date = on_date or today_msk()
    checked_user_ids = {
        r[0]
        for r in db.query(Checkin.user_id).filter(Checkin.checkin_date == on_date.isoformat()).all()
    }
    from app.models import User

    result: dict[int, bool] = {}
    for tg_id in WHITELIST:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        result[tg_id] = bool(user and user.id in checked_user_ids)
    return result


def calendar_days(db: Session, user_id: int, days: int = 90) -> list[dict]:
    """Список последних `days` дней с флагом, была ли отметка — для
    календаря-сетки в Mini App (по типу GitHub contributions). Сетка всегда
    фиксированной ширины (много клеток), даже если реальных отметок пока
    мало — пустые клетки за месяцы до регистрации это нормально, а вот
    подписывать их названием месяца не стоит (см. tracking_since в
    app/api.py и app.js:renderCalendar)."""
    dates = _checkin_dates(db, user_id)
    end = today_msk()
    start = end - timedelta(days=days - 1)

    result = []
    d = start
    while d <= end:
        result.append({"date": d.isoformat(), "checked": d.isoformat() in dates})
        d += timedelta(days=1)
    return result
