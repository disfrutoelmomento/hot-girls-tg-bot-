"""Создание объектов Bot и Dispatcher вынесено в отдельный модуль от
регистрации хендлеров (см. app/bot.py), чтобы app/notify.py мог
импортировать bot и использовать его для отправки сообщений в группу без
циклического импорта (notify нужен хендлерам, а хендлеры регистрируются в
app/bot.py)."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
