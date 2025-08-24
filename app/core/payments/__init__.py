from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

from aiogram import Bot, types
from sqlalchemy.orm import Session

from app.db.models import Entitlement, Order


@dataclass(frozen=True)
class Product:
    """Representation of a sellable product."""

    product_id: str
    title: str
    amount_xtr: int
    quota: int
    duration_days: int | None
    fair_daily_cap: int


PRODUCT_CATALOG: Dict[str, Product] = {
    "pack_3": Product(
        product_id="pack_3",
        title="3 Requests",
        amount_xtr=300,
        quota=3,
        duration_days=None,
        fair_daily_cap=3,
    ),
    "pack_10": Product(
        product_id="pack_10",
        title="10 Requests",
        amount_xtr=900,
        quota=10,
        duration_days=None,
        fair_daily_cap=5,
    ),
    "unlimited_30d": Product(
        product_id="unlimited_30d",
        title="Unlimited 30d",
        amount_xtr=3000,
        quota=0,
        duration_days=30,
        fair_daily_cap=20,
    ),
    "sub_30d": Product(
        product_id="sub_30d",
        title="Subscription 30d",
        amount_xtr=1500,
        quota=30,
        duration_days=30,
        fair_daily_cap=5,
    ),
}


class PaymentError(Exception):
    """Raised when payment processing fails."""


def create_order(session: Session, user_id: int, product_id: str) -> Order:
    """Create a new order for the given product."""

    product = PRODUCT_CATALOG.get(product_id)
    if product is None:
        raise PaymentError("unknown product")
    order = Order(
        id=int(datetime.utcnow().timestamp() * 1000),
        user_id=user_id,
        product=product_id,
        amount_xtr=product.amount_xtr,
        currency="XTR",
        status="pending",
    )
    session.add(order)
    session.commit()
    return order


async def send_product_invoice(bot: Bot, chat_id: int, order: Order) -> types.Message:
    """Send a Telegram invoice for the specified order."""

    product = PRODUCT_CATALOG[order.product]
    price = types.LabeledPrice(label=product.title, amount=product.amount_xtr)
    return await bot.send_invoice(
        chat_id=chat_id,
        title=product.title,
        description=product.title,
        payload=str(order.id),
        currency="XTR",
        prices=[price],
    )


async def handle_pre_checkout(query: types.PreCheckoutQuery, session: Session) -> None:
    """Process pre-checkout queries from Telegram."""

    order = session.get(Order, int(query.invoice_payload))
    if order is None:
        await query.answer(ok=False, error_message="order not found")
        return
    order.status = "pre_checkout"
    session.commit()
    await query.answer(ok=True)


async def handle_successful_payment(message: types.Message, session: Session) -> None:
    """Finalize payment and grant entitlements."""

    sp = message.successful_payment
    if sp is None:
        return

    order = session.get(Order, int(sp.invoice_payload))
    if order is None:
        return

    if order.status == "paid":
        return

    existing = session.get(Entitlement, order.id)
    if existing is not None:
        order.status = "paid"
        session.commit()
        return

    order.status = "paid"
    order.external_id = sp.telegram_payment_charge_id
    product = PRODUCT_CATALOG[order.product]
    expires_at = (
        datetime.utcnow() + timedelta(days=product.duration_days)
        if product.duration_days
        else None
    )
    entitlement = Entitlement(
        id=order.id,
        user_id=order.user_id,
        product=order.product,
        status="active",
        expires_at=expires_at,
        quota_total=product.quota,
        quota_left=product.quota,
        fair_daily_cap=product.fair_daily_cap,
    )
    session.add(entitlement)
    session.commit()


def refund_order(session: Session, order_id: int) -> None:
    """Refund an order and deactivate related entitlements."""

    order = session.get(Order, order_id)
    if order is None:
        raise PaymentError("order not found")
    order.status = "refunded"
    entitlements = (
        session.query(Entitlement)
        .filter(
            Entitlement.user_id == order.user_id,
            Entitlement.product == order.product,
            Entitlement.status == "active",
        )
        .all()
    )
    for ent in entitlements:
        ent.status = "cancelled"
    session.commit()
