"""Постоянная клавиатура-меню внизу чата — чтобы не нужно было помнить и
печатать команды. Показывается после /start.

Кнопка трекера сюда специально не добавляется: у обычной кнопки на
custom-клавиатуре (в отличие от inline-кнопки или Menu Button) нет
initData, поэтому Mini App не смог бы авторизовать пользователя. Вместо
этого трекер открывается через кнопку-меню (см. app/api.py, lifespan)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

PLAN_BUTTON_TEXT = "План на неделю"
WEBAPP_BUTTON_TEXT = "Открыть трекер"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=PLAN_BUTTON_TEXT)]], resize_keyboard=True)
