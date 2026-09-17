"""Постоянная клавиатура-меню внизу чата — чтобы не нужно было помнить и
печатать команды. Показывается после /start.

У кнопки "Открыть трекер" здесь нет web_app: у обычной кнопки на
custom-клавиатуре (в отличие от inline-кнопки или Menu Button) нет
initData, поэтому Mini App не смог бы авторизовать пользователя. Вместо
этого при нажатии бот присылает inline-кнопку — см.
app/handlers/start.py:open_tracker и tracker_inline_keyboard ниже."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import WEBAPP_URL

PLAN_BUTTON_TEXT = "План на неделю"
WEBAPP_BUTTON_TEXT = "Открыть трекер"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=PLAN_BUTTON_TEXT), KeyboardButton(text=WEBAPP_BUTTON_TEXT)]],
        resize_keyboard=True,
    )


def tracker_inline_keyboard() -> InlineKeyboardMarkup | None:
    if not WEBAPP_URL:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=WEBAPP_BUTTON_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
