from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.payments import PRODUCT_CATALOG

EXPERT_BUTTONS = [
    ("🃏 Tarot", "expert:tarot"),
    ("♣ Lenormand", "expert:lenormand"),
    ("ᚱ Runes", "expert:runes"),
    ("✨ Astrology", "expert:astrology"),
    ("🌙 Dreams", "expert:dreams"),
    ("✍️ Copywriter", "expert:copywriter"),
    ("🤖 Assistant", "expert:assistant"),
    ("🔢 Numerology", "expert:numerology"),
]

TARIFF_BUTTON = ("💎 Premium/Payment", "tariffs")
PROFILE_BUTTON = ("👤 Profile/History", "profile")


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, callback in EXPERT_BUTTONS:
        builder.button(text=_(text), callback_data=callback)
    builder.button(text=_(TARIFF_BUTTON[0]), callback_data=TARIFF_BUTTON[1])
    builder.button(text=_(PROFILE_BUTTON[0]), callback_data=PROFILE_BUTTON[1])
    builder.adjust(2)
    return builder.as_markup()


def tariffs_menu() -> InlineKeyboardMarkup:
    """Inline keyboard with available tariff products."""

    builder = InlineKeyboardBuilder()
    for product in PRODUCT_CATALOG.values():
        builder.button(
            text=_(product.title), callback_data=f"buy:{product.product_id}"
        )
    builder.button(text=_("⬅️ Back"), callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()
