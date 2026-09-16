"""Точка входа. Сейчас запускает только бота (polling) — на шаге с
FastAPI и планировщиком этот файл станет запускать всё в одном процессе:
uvicorn (FastAPI) как хозяина процесса, а polling бота и APScheduler —
как фоновые asyncio-задачи внутри него."""

import asyncio
import logging

from app.bot import bot, dp
from app.database import init_db


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
