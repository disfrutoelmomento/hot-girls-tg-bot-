from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DB_PATH


class Base(DeclarativeBase):
    pass


Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# check_same_thread=False нужен, потому что и бот (aiogram), и API (FastAPI),
# и планировщик (APScheduler) обращаются к БД из одного процесса, но не всегда
# из одного и того же потока/задачи. Для SQLite с нашей маленькой нагрузкой
# (3 пользователя) это абсолютно безопасно.
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401 — импорт регистрирует модели в Base.metadata

    Base.metadata.create_all(engine)
