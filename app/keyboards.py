"""Постоянная клавиатура-меню внизу чата — чтобы не нужно было помнить и
печатать команды. Показывается после /start.

Трекер сюда не добавляется: у кнопки на custom-клавиатуре нет initData
(в отличие от Menu Button), поэтому Mini App не смог бы авторизовать
пользователя. Вместо этого трекер открывается через Menu Button
(см. app/api.py, lifespan)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

PLAN_BUTTON_TEXT = "План на неделю"
WEBAPP_BUTTON_TEXT = "Открыть трекер"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=PLAN_BUTTON_TEXT)]], resize_keyboard=True)
