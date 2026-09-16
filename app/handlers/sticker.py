"""Любая из участниц может прислать боту стикер в личку — он автоматически
попадает в общую копилку (таблица stickers) и с этого момента может
случайно выпасть в поздравлении с бейджем или удачным закрытием дня.
Никакого ручного шага (правки кода, перезапуска) не требуется."""

from aiogram import F, Router
from aiogram.types import Message

from app.config import WHITELIST
from app.database import SessionLocal
from app.models import Sticker, User

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(F.sticker)
async def capture_sticker(message: Message) -> None:
    tg_id = message.from_user.id
    if tg_id not in WHITELIST:
        return

    sticker = message.sticker

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if user is None:
            await message.answer("Сначала напиши /start.")
            return

        if db.query(Sticker).filter(Sticker.file_id == sticker.file_id).first() is not None:
            await message.answer("Этот стикер уже есть в копилке 🙂")
            return

        db.add(Sticker(file_id=sticker.file_id, emoji=sticker.emoji, added_by_user_id=user.id))
        db.commit()
        total = db.query(Sticker).count()

    await message.answer(
        f"Стикер добавлен в копилку! Теперь их {total} — буду присылать вразнобой на радостях 🎉"
    )
