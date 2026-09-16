"""Отправка уведомлений в общий групповой чат. Бот пишет в группу только
сам, от своего имени — не читает и не разбирает сообщения участниц там
(этому помогает Privacy Mode бота, включённый по умолчанию в BotFather)."""

from app.bot_instance import bot
from app.config import GROUP_CHAT_ID
from app.texts import badge_awarded_text


async def send_to_group(text: str) -> None:
    await bot.send_message(GROUP_CHAT_ID, text)


async def forward_photo_to_group(photo_file_id: str, caption: str | None = None) -> None:
    await bot.send_photo(GROUP_CHAT_ID, photo_file_id, caption=caption)


async def notify_badge_awarded(name: str, threshold: int) -> None:
    await send_to_group(badge_awarded_text(name, threshold))
