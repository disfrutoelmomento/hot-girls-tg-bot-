"""Постоянная клавиатура-меню внизу чата — чтобы не нужно было помнить и
печатать команды. Показывается после /start."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import WEBAPP_URL

PLAN_BUTTON_TEXT = "План на неделю"
WEBAPP_BUTTON_TEXT = "Открыть трекер"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=PLAN_BUTTON_TEXT)]
    if WEBAPP_URL:
        row.append(KeyboardButton(text=WEBAPP_BUTTON_TEXT, web_app=WebAppInfo(url=WEBAPP_URL)))
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)
