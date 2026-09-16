from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import WEEKDAY_NAMES_RU, WEEKDAY_SHORT_RU, WHITELIST
from app.database import SessionLocal
from app.models import User, WeeklyPlan

router = Router()
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

# "пн"/"понедельник" -> 0, и так для каждого дня — чтобы разбор текста
# в bulk-режиме понимал и короткую, и полную форму дня недели.
_DAY_ALIASES: dict[str, int] = {}
for _i, (_short, _full) in enumerate(zip(WEEKDAY_SHORT_RU, WEEKDAY_NAMES_RU)):
    _DAY_ALIASES[_short.lower()] = _i
    _DAY_ALIASES[_full.lower()] = _i


class PlanStates(StatesGroup):
    menu = State()
    choosing_day = State()
    entering_activities = State()
    bulk_editing = State()


def _get_user(db, tg_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == tg_id).first()


def _week_plan(db, user_id: int) -> dict[int, list[str]]:
    plan: dict[int, list[str]] = {i: [] for i in range(7)}
    items = (
        db.query(WeeklyPlan)
        .filter(WeeklyPlan.user_id == user_id)
        .order_by(WeeklyPlan.day_of_week, WeeklyPlan.sort_order)
        .all()
    )
    for item in items:
        plan[item.day_of_week].append(item.activity_label)
    return plan


def _format_week_as_text(plan: dict[int, list[str]]) -> str:
    lines = []
    for i, short in enumerate(WEEKDAY_SHORT_RU):
        activities = ", ".join(plan[i]) if plan[i] else "-"
        lines.append(f"{short}: {activities}")
    return "\n".join(lines)


def _parse_week_text(text: str) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {i: [] for i in range(7)}
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        day_part, rest = line.split(":", 1)
        day_idx = _DAY_ALIASES.get(day_part.strip().lower())
        if day_idx is None:
            continue
        rest = rest.strip()
        if rest and rest != "-":
            result[day_idx] = [a.strip() for a in rest.split(",") if a.strip()]
    return result


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить всю неделю одним сообщением", callback_data="plan_bulk")],
            [InlineKeyboardButton(text="Изменить один день", callback_data="plan_pick_day")],
            [InlineKeyboardButton(text="Готово", callback_data="plan_done")],
        ]
    )


def _day_picker_keyboard(plan: dict[int, list[str]]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{day_name} ({len(plan[i])})" if plan[i] else day_name,
            callback_data=f"plan_day:{i}",
        )]
        for i, day_name in enumerate(WEEKDAY_NAMES_RU)
    ]
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="plan_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _show_menu(db, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    plan = _week_plan(db, user_id)
    text = (
        "Твой план на неделю:\n\n"
        f"<code>{escape(_format_week_as_text(plan))}</code>\n\n"
        "Что хочешь сделать?"
    )
    return text, _main_menu_keyboard()


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
        text, kb = await _show_menu(db, user.id)

    await state.set_state(PlanStates.menu)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "plan_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    tg_id = callback.from_user.id
    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        text, kb = await _show_menu(db, user.id)
    await state.set_state(PlanStates.menu)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "plan_bulk")
async def start_bulk_edit(callback: CallbackQuery, state: FSMContext) -> None:
    tg_id = callback.from_user.id
    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        current = _format_week_as_text(_week_plan(db, user.id))

    await state.set_state(PlanStates.bulk_editing)
    await callback.message.edit_text(
        "Пришли план на всю неделю одним сообщением — по одной строке на каждый день:\n"
        "<code>Пн: активность1, активность2</code>\n\n"
        'Если на день ничего не запланировано, поставь "-". '
        "Можно писать и полное название дня, и короткое (Пн / Понедельник).\n\n"
        "Вот твой текущий план — скопируй и отредактируй нужные строки:\n\n"
        f"<code>{escape(current)}</code>"
    )
    await callback.answer()


@router.message(PlanStates.bulk_editing)
async def save_bulk_plan(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    parsed = _parse_week_text(message.text or "")

    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        if user is None:
            await message.answer("Сначала напиши /start.")
            await state.clear()
            return

        db.query(WeeklyPlan).filter(WeeklyPlan.user_id == user.id).delete()
        for day_idx, activities in parsed.items():
            for order, label in enumerate(activities):
                db.add(WeeklyPlan(user_id=user.id, day_of_week=day_idx, activity_label=label, sort_order=order))
        db.commit()
        text, kb = await _show_menu(db, user.id)

    await state.set_state(PlanStates.menu)
    await message.answer(f"План на неделю сохранён.\n\n{text}", reply_markup=kb)


@router.callback_query(F.data == "plan_pick_day")
async def open_day_picker(callback: CallbackQuery, state: FSMContext) -> None:
    tg_id = callback.from_user.id
    with SessionLocal() as db:
        user = _get_user(db, tg_id)
        plan = _week_plan(db, user.id)

    await state.set_state(PlanStates.choosing_day)
    await callback.message.edit_text(
        "Выбери день недели, чтобы настроить план на него "
        "(в скобках — сколько пунктов уже задано):",
        reply_markup=_day_picker_keyboard(plan),
    )
    await callback.answer()


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
        f"Текущий план:\n{escape(current)}\n\n"
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
        plan = _week_plan(db, user.id)

    await state.set_state(PlanStates.choosing_day)
    saved_text = "план на этот день очищен" if not lines else f"сохранено пунктов: {len(lines)}"
    await message.answer(
        f"{WEEKDAY_NAMES_RU[day]}: {saved_text}.\n\nВыбери следующий день или нажми «← Назад».",
        reply_markup=_day_picker_keyboard(plan),
    )


@router.callback_query(F.data == "plan_done")
async def finish_plan(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("План сохранён. В любой момент можно открыть /plan снова.")
    await callback.answer()
