from __future__ import annotations

from datetime import datetime
from typing import cast

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from app.core.payments import PRODUCT_CATALOG, create_order, send_product_invoice
from app.core.telemetry import TelemetryEvent, track
from app.db.models import Entitlement, Usage
from app.db.session import SessionLocal

from .menu import back_menu, main_menu, tariffs_menu

router = Router()


class MainState(StatesGroup):
    menu = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(MainState.menu)
    user = message.from_user
    if user:
        track(TelemetryEvent.START, user_id=user.id)
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
            not entitlement.expires_at or entitlement.expires_at > datetime.utcnow()
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
    await message.answer(text, reply_markup=back_menu())


@router.message(MainState.menu, Command("profile"))
@router.message(MainState.menu, Command("history"))
async def cmd_history(message: Message) -> None:
    user = message.from_user
    if user:
        await _send_history(message, user.id)


@router.callback_query(MainState.menu, F.data == "profile")
async def cb_profile(callback: CallbackQuery) -> None:
    user = callback.from_user
    if callback.message and user:
        msg = cast(Message, callback.message)
        await _send_history(msg, user.id)
    if user:
        track(
            TelemetryEvent.CTA_CLICK,
            user_id=user.id,
            cta="profile",
        )
    await callback.answer()


@router.callback_query(MainState.menu, F.data == "tariffs")
async def cb_tariffs(callback: CallbackQuery) -> None:
    if callback.message:
        lines = [
            _("{title}: {amount} XTR").format(
                title=product.title, amount=product.amount_xtr
            )
            for product in PRODUCT_CATALOG.values()
        ]
        text = _("Available tariff plans:") + "\n" + "\n".join(lines)
        await callback.message.answer(text, reply_markup=tariffs_menu())
    user = callback.from_user
    if user:
        track(
            TelemetryEvent.CTA_CLICK,
            user_id=user.id,
            cta="tariffs",
        )
    await callback.answer()


@router.callback_query(MainState.menu, F.data.startswith("buy:"))
async def cb_buy(callback: CallbackQuery, bot: Bot) -> None:
    data = callback.data or ""
    product_id = data.split(":", 1)[1] if ":" in data else ""
    with SessionLocal() as session:
        order = create_order(
            session, user_id=callback.from_user.id, product_id=product_id
        )
    await send_product_invoice(bot, callback.from_user.id, order)
    user = callback.from_user
    if user:
        track(
            TelemetryEvent.CTA_CLICK,
            user_id=user.id,
            cta=f"buy:{product_id}",
        )
    await callback.answer()


@router.callback_query(MainState.menu, F.data == "back:main")
async def cb_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await callback.message.answer(
            _("Welcome! Use the menu below to choose an expert or view tariffs."),
            reply_markup=main_menu(),
        )
    await state.set_state(MainState.menu)
    user = callback.from_user
    if user:
        track(
            TelemetryEvent.CTA_CLICK,
            user_id=user.id,
            cta="back:main",
        )
    await callback.answer()
