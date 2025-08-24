from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

from aiogram import types
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Session, sessionmaker

from app.core.payments import (
    PRODUCT_CATALOG,
    create_order,
    handle_pre_checkout,
    handle_successful_payment,
    refund_order,
    send_product_invoice,
)
from app.db import models
from app.db.base import Base
from app.db.models import Entitlement, Order, User


def _setup_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    models.JSONB = SQLITE_JSON  # type: ignore[attr-defined]
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def _create_user(session: Session) -> User:
    user = User(id=1, tg_id=1)
    session.add(user)
    session.commit()
    return user


def test_send_invoice_uses_xtr_currency() -> None:
    session = _setup_session()
    user = _create_user(session)
    order = create_order(session, user_id=user.id, product_id="pack_3")
    bot = AsyncMock()
    asyncio.run(send_product_invoice(bot, chat_id=1, order=order))
    bot.send_invoice.assert_awaited()
    args, kwargs = bot.send_invoice.await_args
    assert kwargs["currency"] == "XTR"


def test_pre_checkout_updates_order_status() -> None:
    session = _setup_session()
    user = _create_user(session)
    order = create_order(session, user_id=user.id, product_id="pack_3")
    query = SimpleNamespace(
        invoice_payload=str(order.id),
        answer=AsyncMock(),
    )
    asyncio.run(handle_pre_checkout(cast(types.PreCheckoutQuery, query), session))
    updated = session.get(Order, order.id)
    assert updated is not None
    assert updated.status == "pre_checkout"
    query.answer.assert_awaited_with(ok=True)


def test_successful_payment_creates_entitlement() -> None:
    session = _setup_session()
    user = _create_user(session)
    order = create_order(session, user_id=user.id, product_id="pack_3")
    sp = types.SuccessfulPayment(
        currency="XTR",
        total_amount=order.amount_xtr,
        invoice_payload=str(order.id),
        telegram_payment_charge_id="tpc",
        provider_payment_charge_id="ppc",
    )
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        successful_payment=sp,
    )
    asyncio.run(handle_successful_payment(msg, session))
    updated = session.get(Order, order.id)
    assert updated is not None
    assert updated.status == "paid"
    ent = session.query(Entitlement).one()
    assert ent.quota_total == PRODUCT_CATALOG[order.product].quota


def test_refund_order_cancels_entitlement() -> None:
    session = _setup_session()
    user = _create_user(session)
    order = create_order(session, user_id=user.id, product_id="pack_3")
    sp = types.SuccessfulPayment(
        currency="XTR",
        total_amount=order.amount_xtr,
        invoice_payload=str(order.id),
        telegram_payment_charge_id="tpc",
        provider_payment_charge_id="ppc",
    )
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        successful_payment=sp,
    )
    asyncio.run(handle_successful_payment(msg, session))
    ent = session.query(Entitlement).one()
    refund_order(session, order.id)
    updated_order = session.get(Order, order.id)
    assert updated_order is not None
    assert updated_order.status == "refunded"
    updated_ent = session.get(Entitlement, ent.id)
    assert updated_ent is not None
    assert updated_ent.status == "cancelled"
