from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from .menu import main_menu

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


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await message.answer(_("Profile: no data available."))


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    await message.answer(_("History: no records."))


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(_("Profile: no data available."))
    await callback.answer()


@router.callback_query(F.data == "tariffs")
async def cb_tariffs(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.answer(_("History: no records."))
    await callback.answer()
