"""Отправка уведомлений в общий групповой чат. Бот пишет в группу только
сам, от своего имени — не читает и не разбирает сообщения участниц там
(этому помогает Privacy Mode бота, включённый по умолчанию в BotFather)."""

import random

from aiogram.types import FSInputFile, InputMediaPhoto

from app.bot_instance import bot
from app.config import GROUP_CHAT_ID, MOTIVATION_IMAGES_DIR
from app.texts import BADGE_STICKERS, DAY_SUCCESS_STICKERS, badge_awarded_text


async def send_to_group(text: str) -> None:
    await bot.send_message(GROUP_CHAT_ID, text)


async def forward_photos_to_group(photos: list[tuple[str, str | None]]) -> None:
    """Пересылает несколько фото одним альбомом (media group), а не
    отдельными сообщениями. photos — список (file_id, подпись)."""
    if not photos:
        return
    media = [InputMediaPhoto(media=file_id, caption=caption) for file_id, caption in photos]
    await bot.send_media_group(GROUP_CHAT_ID, media=media)


async def _send_random_sticker(sticker_ids: list[str]) -> None:
    if not sticker_ids:
        return  # список пуст, пока не добавили стикеры (см. app/texts.py)
    await bot.send_sticker(GROUP_CHAT_ID, random.choice(sticker_ids))


async def _send_random_motivation_image() -> None:
    if not MOTIVATION_IMAGES_DIR.exists():
        return
    images = [p for p in MOTIVATION_IMAGES_DIR.iterdir() if p.is_file()]
    if not images:
        return  # папка пуста, пока не положили картинки (см. app/config.py)
    await bot.send_photo(GROUP_CHAT_ID, FSInputFile(random.choice(images)))


async def notify_badge_awarded(name: str, threshold: int) -> None:
    await send_to_group(badge_awarded_text(name, threshold))
    await _send_random_sticker(BADGE_STICKERS)


async def send_celebration_extras() -> None:
    """Опциональный стикер + мотивационная картинка после удачного закрытия
    дня. Оба источника пусты по умолчанию, так что пока ничего не отправят —
    это безопасно, пока контент не добавлен."""
    await _send_random_sticker(DAY_SUCCESS_STICKERS)
    await _send_random_motivation_image()
