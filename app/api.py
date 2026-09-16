"""FastAPI-приложение: отдаёт статику Mini App и один API-эндпоинт с
данными для главного экрана. Здесь же, через lifespan, запускается бот
(polling) и планировщик — так весь процесс на Railway остаётся одним
сервисом на одном порту, без отдельного воркера."""

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram.types import BotCommand
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles

from app.bot import bot, dp
from app.config import BASE_DIR, STREAK_BADGE_THRESHOLDS, WEEKDAY_NAMES_RU, WHITELIST
from app.database import SessionLocal, init_db
from app.models import Badge, Checkin, User, WeeklyPlan
from app.scheduler import setup_scheduler
from app.streaks import calendar_days, group_streak, personal_streak, today_msk, today_quest_status
from app.telegram_auth import validate_init_data

logger = logging.getLogger(__name__)


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

    scheduler = setup_scheduler()
    scheduler.start()
    polling_task = asyncio.create_task(dp.start_polling(bot))

    yield

    polling_task.cancel()
    scheduler.shutdown(wait=False)
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


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
            {"telegram_id": whitelist_tg_id, "name": name, "checked_in_today": quest_status.get(whitelist_tg_id, False)}
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

        return {
            "name": user.name,
            "personal_streak": personal_streak(db, user.id, as_of=today),
            "group_streak": group_streak(db, as_of=today),
            "quest_today": {
                "participants": participants,
                "completed_count": sum(1 for p in participants if p["checked_in_today"]),
                "total": len(participants),
            },
            "plan_today": {
                "day_name": WEEKDAY_NAMES_RU[weekday],
                "activities": [item.activity_label for item in plan_items],
                "completed": checked_in_today,
            },
            "calendar": calendar_days(db, user.id, days=90),
            "badges": [
                {"threshold": t, "unlocked": t in earned_thresholds}
                for t in STREAK_BADGE_THRESHOLDS
            ],
        }


# Регистрируем API-роуты до монтирования статики: иначе Mini App (index.html
# на "/") перехватит вообще все пути, включая /api/dashboard.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "webapp"), html=True), name="webapp")
