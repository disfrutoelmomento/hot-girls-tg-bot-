from aiogram import F, Router
from aiogram.types import Message

from app.config import STREAK_BADGE_THRESHOLDS, WHITELIST
from app.database import SessionLocal
from app.models import Badge, Checkin, User
from app.notify import notify_badge_awarded
from app.streaks import personal_streak, today_msk

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    tg_id = message.from_user.id
    if tg_id not in WHITELIST:
        return

    today = today_msk().isoformat()
    # Берём file_id самого крупного размера фото; сам файл не скачиваем —
    # Telegram и так хранит его, file_id достаточно, чтобы позже переслать.
    photo_file_id = message.photo[-1].file_id

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user is None:
            await message.answer("Сначала напиши /start.")
            return

        existing = (
            db.query(Checkin)
            .filter(Checkin.user_id == user.id, Checkin.checkin_date == today)
            .first()
        )
        if existing is not None:
            await message.answer("Сегодняшний день уже отмечен — повторное фото не нужно.")
            return

        db.add(Checkin(user_id=user.id, checkin_date=today, photo_file_id=photo_file_id))
        db.commit()

        streak = personal_streak(db, user.id)

        new_badge_threshold = None
        if streak in STREAK_BADGE_THRESHOLDS:
            already_awarded = (
                db.query(Badge)
                .filter(Badge.user_id == user.id, Badge.threshold == streak)
                .first()
            )
            if already_awarded is None:
                db.add(Badge(user_id=user.id, threshold=streak))
                db.commit()
                new_badge_threshold = streak

        name = user.name

    await message.answer(f"Готово! День отмечен. Личный стрик: {streak} дн. подряд.")

    if new_badge_threshold:
        await notify_badge_awarded(name, new_badge_threshold)

    # TODO: пересылка фото и подведение итога группового квеста происходит
    # не здесь, а в джобе закрытия дня в 23:59 (см. app/scheduler.py) —
    # так делаем один согласованный момент подведения итога, а не по факту
    # прихода каждого фото.
