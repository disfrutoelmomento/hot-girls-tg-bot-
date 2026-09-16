"""Точка входа. Сейчас запускает бота (polling) и планировщик в одном
процессе. На шаге с FastAPI этот файл станет запускать всё в одном
процессе: uvicorn (FastAPI) как хозяина процесса, а polling бота и
APScheduler — как фоновые asyncio-задачи внутри него."""

import asyncio
import logging

from aiogram.types import BotCommand

from app.bot import bot, dp
from app.database import init_db
from app.scheduler import setup_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()

    # Список команд для "/"-меню Telegram рядом с полем ввода.
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Зарегистрироваться / начать"),
            BotCommand(command="plan", description="Настроить план на неделю"),
        ]
    )

    scheduler = setup_scheduler()
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
