from __future__ import annotations

from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from app.core.payments import create_order, send_product_invoice
from app.db.models import Entitlement, Usage
from app.db.session import SessionLocal

from .menu import main_menu, tariffs_menu

router = Router()


class MainState(StatesGroup):
    menu = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(MainState.menu)
    await message.answer(
        _("Welcome! Use the menu below to choose an expert or view tariffs."),
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        _(
            "Help: This bot provides astrological readings and other services. "
            "Use the menu or commands."
        )
    )


def _history_and_quota(user_id: int) -> tuple[int, list[str]]:
    """Retrieve remaining quota and last usage records."""

    with SessionLocal() as session:
        entitlement = (
            session.query(Entitlement)
            .filter(Entitlement.user_id == user_id, Entitlement.status == "active")
            .order_by(Entitlement.created_at.desc())
            .first()
        )
        quota = 0
        if entitlement and (
            not entitlement.expires_at
            or entitlement.expires_at > datetime.utcnow()
        ):
            quota = entitlement.quota_left
        usages = (
            session.query(Usage)
            .filter(Usage.user_id == user_id)
            .order_by(Usage.created_at.desc())
            .limit(5)
            .all()
        )
    lines = [f"{u.created_at:%Y-%m-%d %H:%M} — {u.expert} (-{u.cost})" for u in usages]
    return quota, lines


async def _send_history(message: Message, user_id: int) -> None:
    quota, lines = _history_and_quota(user_id)
    if lines:
        history_text = "\n".join(lines)
    else:
        history_text = _("No usage yet.")
    text = _("Your remaining quota: {quota}").format(quota=quota)
    text += "\n" + _("Usage history:") + "\n" + history_text
    await message.answer(text)


@router.message(MainState.menu, Command("profile"))
@router.message(MainState.menu, Command("history"))
async def cmd_history(message: Message) -> None:
    await _send_history(message, message.from_user.id)


@router.callback_query(MainState.menu, F.data == "profile")
async def cb_profile(callback: CallbackQuery) -> None:
    if callback.message:
        await _send_history(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(MainState.menu, F.data == "tariffs")
async def cb_tariffs(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(
            _("Available tariff plans:"), reply_markup=tariffs_menu()
        )
    await callback.answer()


@router.callback_query(MainState.menu, F.data.startswith("buy:"))
async def cb_buy(callback: CallbackQuery, bot: Bot) -> None:
    product_id = callback.data.split(":", 1)[1]
    with SessionLocal() as session:
        order = create_order(
            session, user_id=callback.from_user.id, product_id=product_id
        )
    await send_product_invoice(bot, callback.from_user.id, order)
    await callback.answer()


@router.callback_query(MainState.menu, F.data == "back:main")
async def cb_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await callback.message.answer(
            _("Welcome! Use the menu below to choose an expert or view tariffs."),
            reply_markup=main_menu(),
        )
    await state.set_state(MainState.menu)
    await callback.answer()
