"""Catch-all handlers. MUST be the last router registered."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.i18n import t

router = Router(name="common")


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    """Non-actionable buttons (page counter, locked chapters) just dismiss."""
    await callback.answer()


@router.callback_query()
async def expired_callback(callback: CallbackQuery, lang: str) -> None:
    """A button from an old message whose handler no longer matches."""
    await callback.answer(t(lang, "alert_not_found"), show_alert=True)
