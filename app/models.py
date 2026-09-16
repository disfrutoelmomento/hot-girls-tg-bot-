from datetime import datetime, timezone

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(Base):
    """Одна из трёх фиксированных участниц. Создаётся при /start, если её
    telegram_id есть в WHITELIST (см. config.py)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=_now_iso)

    checkins: Mapped[list["Checkin"]] = relationship(back_populates="user")
    plan_items: Mapped[list["WeeklyPlan"]] = relationship(back_populates="user")
    badges: Mapped[list["Badge"]] = relationship(back_populates="user")


class Checkin(Base):
    """Отметка тренировки: одно фото = один закрытый день для пользователя.
    photo_file_id — это file_id из Telegram, сам файл не скачиваем и не
    храним — Telegram и так хранит его бессрочно, а file_id достаточно,
    чтобы позже переслать это же фото (например в групповой чат)."""

    __tablename__ = "checkins"
    __table_args__ = (UniqueConstraint("user_id", "checkin_date", name="uq_user_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    checkin_date: Mapped[str] = mapped_column(index=True)  # 'YYYY-MM-DD' по Europe/Moscow
    photo_file_id: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=_now_iso)

    user: Mapped["User"] = relationship(back_populates="checkins")


class WeeklyPlan(Base):
    """Один пункт недельного плана одной участницы на один день недели.
    Носит информационный характер — не влияет на закрытие дня (см. ТЗ)."""

    __tablename__ = "weekly_plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    day_of_week: Mapped[int]  # 0=Понедельник ... 6=Воскресенье
    activity_label: Mapped[str]
    sort_order: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="plan_items")


class Badge(Base):
    """Факт выдачи бейджа за личный стрик. UNIQUE защищает от повторного
    поздравления с одним и тем же порогом (3/7/14/30 дней)."""

    __tablename__ = "badges"
    __table_args__ = (UniqueConstraint("user_id", "threshold", name="uq_user_threshold"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    threshold: Mapped[int]
    awarded_at: Mapped[str] = mapped_column(default=_now_iso)

    user: Mapped["User"] = relationship(back_populates="badges")


class DayResult(Base):
    """Итог дня, который проставляет планировщик в 23:59. Нужен не для
    расчёта стрика (его мы считаем на лету из checkins), а чтобы:
    - не отправить уведомление о закрытии дня дважды при перезапуске бота;
    - быстро поднимать историю групповых квестов для календаря/статистики."""

    __tablename__ = "day_results"

    date: Mapped[str] = mapped_column(primary_key=True)  # 'YYYY-MM-DD'
    all_completed: Mapped[bool]
    notified_at: Mapped[str] = mapped_column(default=_now_iso)
