from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import WHITELIST
from app.database import SessionLocal
from app.keyboards import WEBAPP_BUTTON_TEXT, main_menu_keyboard, tracker_inline_keyboard
from app.models import User

router = Router()
# Хендлеры этого роутера реагируют только на личку — в группе бот не
# должен читать/разбирать сообщения участниц (privacy mode).
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tg_id = message.from_user.id

    if tg_id not in WHITELIST:
        await message.answer(
            "Привет! Этот бот приватный — доступен только участницам закрытой группы. "
            "Если это ошибка, попроси добавить твой telegram_id в конфиг бота."
        )
        return

    name = WHITELIST[tg_id]
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user is None:
            user = User(telegram_id=tg_id, name=name)
            db.add(user)
            db.commit()
            greeting = f"Привет, {name}! Зарегистрировала тебя."
        else:
            greeting = f"С возвращением, {name}!"

    text = (
        f"{greeting}\n\n"
        "Как это работает:\n"
        "— Пришли сюда фото после тренировки — оно закроет день и продлит твой стрик.\n"
        "— Кнопки внизу — настроить план на неделю и открыть трекер."
    )

    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text == WEBAPP_BUTTON_TEXT)
async def open_tracker(message: Message) -> None:
    # У кнопки на обычной (reply) клавиатуре нет initData — только у
    # inline-кнопки или Menu Button (см. app/keyboards.py). Поэтому сама
    # reply-кнопка не открывает Mini App напрямую, а присылает inline-кнопку,
    # которая уже открывает трекер с рабочей авторизацией.
    tracker_kb = tracker_inline_keyboard()
    if tracker_kb is None:
        await message.answer("Трекер пока не настроен.")
        return
    await message.answer("Трекер:", reply_markup=tracker_kb)
