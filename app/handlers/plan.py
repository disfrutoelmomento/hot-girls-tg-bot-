from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import WEEKDAY_NAMES_RU, WHITELIST
from app.database import SessionLocal
from app.models import User, WeeklyPlan

router = Router()
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


class PlanStates(StatesGroup):
    choosing_day = State()
    entering_activities = State()


def _get_user(db, tg_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == tg_id).first()


def _day_keyboard(db, user_id: int) -> InlineKeyboardMarkup:
    counts = {i: 0 for i in range(7)}
    for (day,) in db.query(WeeklyPlan.day_of_week).filter(WeeklyPlan.user_id == user_id).all():
        counts[day] += 1

    buttons = [
        [InlineKeyboardButton(
            text=f"{day_name} ({counts[i]})" if counts[i] else day_name,
            callback_data=f"plan_day:{i}",
        )]
        for i, day_name in enumerate(WEEKDAY_NAMES_RU)
    ]
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="plan_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("plan"))
async def cmd_plan(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    if tg_id not in WHITELIST:
        return

    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        if user is None:
            await message.answer("Сначала напиши /start.")
            return
        kb = _day_keyboard(db, user.id)

    await state.set_state(PlanStates.choosing_day)
    await message.answer(
        "Выбери день недели, чтобы настроить план активностей на него.\n"
        "В скобках — сколько пунктов уже задано на этот день:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("plan_day:"))
async def choose_day(callback: CallbackQuery, state: FSMContext) -> None:
    day = int(callback.data.split(":", 1)[1])
    tg_id = callback.from_user.id

    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        if user is None:
            await callback.answer("Сначала напиши /start в личку боту.", show_alert=True)
            return
        items = (
            db.query(WeeklyPlan)
            .filter(WeeklyPlan.user_id == user.id, WeeklyPlan.day_of_week == day)
            .order_by(WeeklyPlan.sort_order)
            .all()
        )

    current = "\n".join(f"• {item.activity_label}" for item in items) or "(пока пусто)"
    await state.update_data(day=day)
    await state.set_state(PlanStates.entering_activities)
    await callback.message.edit_text(
        f"{WEEKDAY_NAMES_RU[day]}\n"
        f"Текущий план:\n{current}\n\n"
        "Пришли новый список активностей одним сообщением, каждая — с новой строки.\n"
        'Чтобы очистить план на этот день, отправь "-".'
    )
    await callback.answer()


@router.message(PlanStates.entering_activities)
async def save_activities(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    day = data["day"]
    tg_id = message.from_user.id
    text = (message.text or "").strip()

    lines = [] if text == "-" else [line.strip() for line in text.splitlines() if line.strip()]

    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        if user is None:
            await message.answer("Сначала напиши /start.")
            await state.clear()
            return

        db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user.id, WeeklyPlan.day_of_week == day
        ).delete()
        for order, label in enumerate(lines):
            db.add(WeeklyPlan(user_id=user.id, day_of_week=day, activity_label=label, sort_order=order))
        db.commit()
        kb = _day_keyboard(db, user.id)

    await state.set_state(PlanStates.choosing_day)
    saved_text = "план на этот день очищен" if not lines else f"сохранено пунктов: {len(lines)}"
    await message.answer(
        f"{WEEKDAY_NAMES_RU[day]}: {saved_text}.\n\nВыбери следующий день или нажми «Готово».",
        reply_markup=kb,
    )


@router.callback_query(F.data == "plan_done")
async def finish_plan(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("План сохранён. В любой момент можно открыть /plan снова.")
    await callback.answer()
