from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import WEBAPP_URL, WHITELIST
from app.database import SessionLocal
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
        "— /plan — настроить план активностей на каждый день недели.\n"
        "— Кнопка ниже открывает трекер со стриками, квестом дня и бейджами."
    )

    kb = None
    if WEBAPP_URL:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть трекер", web_app=WebAppInfo(url=WEBAPP_URL))]
            ]
        )

    await message.answer(text, reply_markup=kb)
