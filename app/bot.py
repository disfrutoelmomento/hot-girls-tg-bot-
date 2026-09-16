"""Регистрация роутеров-хендлеров на диспетчере. Импортируется отдельно от
app.bot_instance, чтобы избежать циклического импорта: хендлеры используют
app.notify, а notify использует bot из bot_instance, а не отсюда."""

from app.bot_instance import bot, dp
from app.handlers import photo, plan, start

dp.include_router(start.router)
dp.include_router(plan.router)
dp.include_router(photo.router)

__all__ = ["bot", "dp"]
