"""Проверка initData, которую Telegram WebApp SDK передаёт из Mini App.

Без этой проверки любой человек мог бы подделать запрос к API, просто
подставив чужой telegram_id в тело запроса. Алгоритм — официальный, из
документации Telegram: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException

from app.config import BOT_TOKEN

MAX_INIT_DATA_AGE_SECONDS = 24 * 60 * 60


def validate_init_data(init_data: str) -> dict:
    """Возвращает dict с данными пользователя Telegram (id, first_name, ...)
    или бросает HTTPException(401), если подпись неверна/просрочена."""
    if not init_data:
        raise HTTPException(status_code=401, detail="Нет initData")

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        raise HTTPException(status_code=401, detail="Некорректный initData")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Нет подписи в initData")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status_code=401, detail="Неверная подпись initData")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > MAX_INIT_DATA_AGE_SECONDS:
        raise HTTPException(status_code=401, detail="initData устарела, открой трекер заново")

    try:
        return json.loads(parsed["user"])
    except (KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Нет данных пользователя в initData")
