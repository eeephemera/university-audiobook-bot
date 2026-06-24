"""Shared handler helpers."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def show_screen(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Render a navigation screen from a callback.

    Edits the message in place when it is an editable text message (smooth,
    no chat spam). Falls back to sending a new message when the source is media
    (e.g. the button lived under an audio chapter), is too old to edit, or is a
    forwarded copy the bot doesn't own.
    """
    message = callback.message
    if message is None:
        return
    if message.text is not None:
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=reply_markup)
