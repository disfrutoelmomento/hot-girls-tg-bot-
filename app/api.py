"""FastAPI-приложение: отдаёт статику Mini App и один API-эндпоинт с
данными для главного экрана. Здесь же, через lifespan, запускается бот
(polling) и планировщик — так весь процесс на Railway остаётся одним
сервисом на одном порту, без отдельного воркера."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.staticfiles import StaticFiles

from app.bot import bot, dp
from app.config import (
    BASE_DIR,
    STREAK_BADGE_THRESHOLDS,
    TIMEZONE,
    WEBAPP_URL,
    WEEKDAY_NAMES_EN,
    WHITELIST,
    theme_for_name,
)
from app.database import SessionLocal, init_db
from app.keyboards import WEBAPP_BUTTON_TEXT
from app.models import Badge, Checkin, User, WeeklyPlan
from app.scheduler import setup_scheduler
from app.streaks import calendar_days, group_streak, personal_streak, today_msk, today_quest_status
from app.telegram_auth import validate_init_data

logger = logging.getLogger(__name__)

# tg_id -> (jpeg bytes, expires_at). Профильные фото меняются редко —
# час кэша избавляет от лишних походов в Telegram API на каждый визит в Mini App.
_AVATAR_CACHE: dict[int, tuple[bytes, float]] = {}
_AVATAR_CACHE_TTL = 3600


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    init_db()

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Зарегистрироваться / начать"),
            BotCommand(command="plan", description="Настроить план на неделю"),
        ]
    )
    if WEBAPP_URL:
        # Menu Button (иконка рядом с полем ввода) — единственный способ
        # открыть Mini App в один тап и с рабочим initData: у кнопки на
        # ReplyKeyboardMarkup initData нет (см. app/keyboards.py).
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text=WEBAPP_BUTTON_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))
        )

    scheduler = setup_scheduler()
    scheduler.start()
    polling_task = asyncio.create_task(dp.start_polling(bot))

    yield

    polling_task.cancel()
    scheduler.shutdown(wait=False)
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/api/avatar/{tg_id}")
async def get_avatar(tg_id: int) -> Response:
    if tg_id not in WHITELIST:
        raise HTTPException(status_code=404)

    cached = _AVATAR_CACHE.get(tg_id)
    if cached and cached[1] > time.monotonic():
        return Response(content=cached[0], media_type="image/jpeg")

    photos = await bot.get_user_profile_photos(tg_id, limit=1)
    if photos.total_count == 0:
        raise HTTPException(status_code=404)

    file = await bot.get_file(photos.photos[0][-1].file_id)
    buf = await bot.download_file(file.file_path)
    content = buf.read()
    _AVATAR_CACHE[tg_id] = (content, time.monotonic() + _AVATAR_CACHE_TTL)
    return Response(content=content, media_type="image/jpeg")


@app.get("/api/dashboard")
async def get_dashboard(x_telegram_init_data: str = Header(...)) -> dict:
    tg_user = validate_init_data(x_telegram_init_data)
    tg_id = tg_user.get("id")

    if tg_id not in WHITELIST:
        raise HTTPException(status_code=403, detail="Эта участница не в списке")

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Сначала напиши /start боту")

        today = today_msk()
        checked_in_today = (
            db.query(Checkin)
            .filter(Checkin.user_id == user.id, Checkin.checkin_date == today.isoformat())
            .first()
            is not None
        )

        quest_status = today_quest_status(db, today)
        participants = [
            {
                "telegram_id": whitelist_tg_id,
                "name": name,
                "theme": theme_for_name(name),
                "checked_in_today": quest_status.get(whitelist_tg_id, False),
            }
            for whitelist_tg_id, name in WHITELIST.items()
        ]

        weekday = today.weekday()
        plan_items = (
            db.query(WeeklyPlan)
            .filter(WeeklyPlan.user_id == user.id, WeeklyPlan.day_of_week == weekday)
            .order_by(WeeklyPlan.sort_order)
            .all()
        )

        earned_thresholds = {
            b.threshold for b in db.query(Badge).filter(Badge.user_id == user.id).all()
        }

        streak = personal_streak(db, user.id, as_of=today)
        next_threshold = next(
            (t for t in STREAK_BADGE_THRESHOLDS if t not in earned_thresholds), None
        )
        # Календарь начинается с 1-го числа месяца регистрации и растёт
        # вправо по мере времени (сентябрь → октябрь → ...), а не тянет
        # почти 3 месяца пустых клеток до того, как бот вообще существовал.
        registered_date = datetime.fromisoformat(user.created_at).astimezone(TIMEZONE).date()
        calendar_since = registered_date.replace(day=1)

        return {
            "name": user.name,
            "theme": theme_for_name(user.name),
            "personal_streak": streak,
            "group_streak": group_streak(db, as_of=today),
            "next_badge": (
                {"threshold": next_threshold, "days_left": max(next_threshold - streak, 0)}
                if next_threshold is not None
                else None
            ),
            "quest_today": {
                "participants": participants,
                "completed_count": sum(1 for p in participants if p["checked_in_today"]),
                "total": len(participants),
            },
            "plan_today": {
                "day_name": WEEKDAY_NAMES_EN[weekday],
                "activities": [item.activity_label for item in plan_items],
                "completed": checked_in_today,
            },
            "calendar": calendar_days(db, user.id, days=90, since=calendar_since),
            "badges": [
                {"threshold": t, "unlocked": t in earned_thresholds}
                for t in STREAK_BADGE_THRESHOLDS
            ],
        }


# Регистрируем API-роуты до монтирования статики: иначе Mini App (index.html
# на "/") перехватит вообще все пути, включая /api/dashboard.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "webapp"), html=True), name="webapp")
