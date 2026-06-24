"""Shared handler helpers for callback-driven navigation.

Screens are mostly text and we edit them in place (smooth, no chat spam). But the
book card can be a *photo* (cover), and you can't edit a text message into a photo
(or vice-versa). So when the message type doesn't match the target we delete the
old navigation message and send a fresh one — while never deleting *content*
messages (audio albums, PDF) so the user keeps them.
"""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def _leave(message) -> None:
    """Remove the current navigation screen before sending a new one.

    Deletes only text screens and photo cards; keeps audio/PDF (content).
    """
    if message is None:
        return
    if message.text is not None or message.photo:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass


async def show_screen(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Show a text screen: edit in place if possible, else replace."""
    message = callback.message
    if message is not None and message.text is not None:
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return
        except TelegramBadRequest:
            pass
    await _leave(message)
    if message is not None:
        await message.answer(text, reply_markup=reply_markup)


async def show_photo_screen(
    callback: CallbackQuery,
    photo_id: str,
    caption: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Show a screen backed by a photo (the book cover) + caption + buttons."""
    message = callback.message
    if message is None:
        return
    await _leave(message)
    await message.answer_photo(photo_id, caption=caption, reply_markup=reply_markup)
