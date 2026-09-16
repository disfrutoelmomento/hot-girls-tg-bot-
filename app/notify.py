"""Отправка уведомлений в общий групповой чат. Бот пишет в группу только
сам, от своего имени — не читает и не разбирает сообщения участниц там
(этому помогает Privacy Mode бота, включённый по умолчанию в BotFather)."""

import random

from aiogram.types import FSInputFile, InputMediaPhoto

from app.bot_instance import bot
from app.config import GROUP_CHAT_ID, MOTIVATION_IMAGES_DIR
from app.database import SessionLocal
from app.models import Sticker
from app.texts import badge_awarded_text


async def send_to_group(text: str) -> None:
    await bot.send_message(GROUP_CHAT_ID, text)


async def forward_photos_to_group(photos: list[tuple[str, str | None]]) -> None:
    """Пересылает несколько фото одним альбомом (media group), а не
    отдельными сообщениями. photos — список (file_id, подпись)."""
    if not photos:
        return
    media = [InputMediaPhoto(media=file_id, caption=caption) for file_id, caption in photos]
    await bot.send_media_group(GROUP_CHAT_ID, media=media)


async def send_random_sticker() -> None:
    """Один общий пул стикеров, копится сам (см. app/handlers/sticker.py).
    Вызывается только из тех мест, где стикер уместен (бейдж, утреннее
    приветствие, удачное закрытие дня) — не из всех уведомлений подряд.
    Пока копилка пуста — безопасный no-op."""
    with SessionLocal() as db:
        file_ids = [row[0] for row in db.query(Sticker.file_id).all()]
    if not file_ids:
        return
    await bot.send_sticker(GROUP_CHAT_ID, random.choice(file_ids))


async def send_random_motivation_image() -> None:
    if not MOTIVATION_IMAGES_DIR.exists():
        return
    images = [p for p in MOTIVATION_IMAGES_DIR.iterdir() if p.is_file()]
    if not images:
        return  # папка пуста, пока не положили картинки (см. app/config.py)
    await bot.send_photo(GROUP_CHAT_ID, FSInputFile(random.choice(images)))


async def notify_badge_awarded(name: str, threshold: int) -> None:
    await send_to_group(badge_awarded_text(name, threshold))
    await send_random_sticker()


async def send_celebration_extras() -> None:
    """Опциональный стикер + мотивационная картинка после удачного
    закрытия дня. Пока ничего не добавлено — оба шага безопасный no-op."""
    await send_random_sticker()
    await send_random_motivation_image()
