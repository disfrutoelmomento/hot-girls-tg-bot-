from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import WHITELIST
from app.database import SessionLocal
from app.keyboards import main_menu_keyboard
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
