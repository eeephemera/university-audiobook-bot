"""Chapters grid (all parts on one screen) + single-chapter playback + play-all.

Tapping "Listen" opens one screen with every part as a header and its chapters
as number buttons. Tapping a chapter plays it with reliable Prev/Next nav
(works the same on every client, unlike Telegram's album auto-advance).
"""

from __future__ import annotations

import asyncio
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.callbacks import ChapterCB
from app.handlers._helpers import show_screen
from app.i18n import loc, t
from app.keyboards.inline import chapters_overview_keyboard, playall_done_keyboard
from app.services import CatalogService
from app.services.delivery import send_all_chapters, send_chapter

router = Router(name="chapter")
log = logging.getLogger(__name__)

# Strong refs to in-flight background senders so the loop's GC can't cancel them.
_background_tasks: set[asyncio.Task] = set()

# The single "now playing" audio message per chat. We keep ONE chapter audio in
# the chat at a time (delete the previous one before sending the next) so the
# Telegram player has no adjacent audio to auto-jump to — navigation is explicit
# via the Prev/Next buttons. (Lost on restart; a stale message just won't delete.)
_now_playing: dict[int, int] = {}


def _part_title(book, section: int, lang: str) -> str:
    return loc((book.sections or {}).get(str(section)), lang)


@router.callback_query(ChapterCB.filter(F.action == "list"))
async def list_chapters(
    callback: CallbackQuery,
    callback_data: ChapterCB,
    catalog: CatalogService,
    user,
    lang: str,
) -> None:
    book = await catalog.get_book(callback_data.book_id)
    if book is None:
        await callback.answer(t(lang, "alert_not_found"), show_alert=True)
        return
    chapters = await catalog.chapters_of(book.id)
    if not any(c.is_ready for c in chapters):
        await callback.answer(t(lang, "alert_not_ready"), show_alert=True)
        return

    listened = await catalog.listened(user.id, book.id) if user else set()
    title = t(lang, "chapters_title", book=escape(loc(book.title, lang)))
    text = f"{title}\n\n<i>{t(lang, 'chapters_hint')}</i>"
    kb = chapters_overview_keyboard(book, chapters, listened, callback_data.page, lang)
    await show_screen(callback, text, kb)
    await callback.answer()


@router.callback_query(ChapterCB.filter(F.action == "play"))
async def play_chapter(
    callback: CallbackQuery,
    callback_data: ChapterCB,
    bot: Bot,
    catalog: CatalogService,
    user,
    lang: str,
) -> None:
    book = await catalog.get_book(callback_data.book_id)
    if book is None:
        await callback.answer(t(lang, "alert_not_found"), show_alert=True)
        return
    chapters = await catalog.chapters_of(book.id)
    chapter = next(
        (c for c in chapters if c.section == callback_data.section and c.number == callback_data.number),
        None,
    )
    if chapter is None or not chapter.is_ready:
        await callback.answer(t(lang, "alert_not_ready"), show_alert=True)
        return

    show_part = len(await catalog.sections_present(book.id)) > 1
    ordered_ready = [(c.section, c.number) for c in chapters if c.is_ready]
    chat_id = callback.message.chat.id

    # Keep only one chapter audio in the chat: drop the previous one first.
    previous = _now_playing.pop(chat_id, None)
    if previous is not None:
        try:
            await bot.delete_message(chat_id, previous)
        except TelegramBadRequest:
            pass

    message = await send_chapter(
        bot,
        chat_id,
        book,
        chapter,
        lang,
        ordered_ready=ordered_ready,
        show_part=show_part,
        part_title=_part_title(book, chapter.section, lang) if show_part else "",
    )
    _now_playing[chat_id] = message.message_id
    if user is not None:
        await catalog.save_progress(user.id, book.id, chapter.section, chapter.number)
    await callback.answer()


async def _deliver_sequence(bot, chat_id, book, chapters, lang, show_part, done_kb) -> None:
    try:
        sent = await send_all_chapters(bot, chat_id, book, chapters, lang, show_part=show_part)
        await bot.send_message(chat_id, t(lang, "playall_done", n=sent), reply_markup=done_kb)
    except Exception:  # noqa: BLE001
        log.exception("play-all failed (book=%s chat=%s)", book.id, chat_id)
        try:
            await bot.send_message(chat_id, t(lang, "playall_error"))
        except Exception:  # noqa: BLE001
            pass


@router.callback_query(ChapterCB.filter(F.action == "playall"))
async def play_all(
    callback: CallbackQuery,
    callback_data: ChapterCB,
    bot: Bot,
    catalog: CatalogService,
    lang: str,
) -> None:
    book = await catalog.get_book(callback_data.book_id)
    if book is None:
        await callback.answer(t(lang, "alert_not_found"), show_alert=True)
        return

    chapters = await catalog.chapters_of(book.id)
    if callback_data.section:  # 0 == whole book
        chapters = [c for c in chapters if c.section == callback_data.section]
    ready = [c for c in chapters if c.is_ready]
    if not ready:
        await callback.answer(t(lang, "alert_not_ready"), show_alert=True)
        return

    show_part = len(await catalog.sections_present(book.id)) > 1
    await callback.answer(t(lang, "playall_sending"))
    done_kb = playall_done_keyboard(book.id, lang)
    task = asyncio.create_task(
        _deliver_sequence(bot, callback.message.chat.id, book, ready, lang, show_part, done_kb)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
