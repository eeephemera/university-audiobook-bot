"""Parts selection + play-all.

Flow is deliberately minimal — no per-chapter picking:
  • multi-part book: tap "Listen" -> choose a part -> that part's audio drops in
  • single-part book: tap "Listen" -> the audio drops in straight away
"""

from __future__ import annotations

import asyncio
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.callbacks import ChapterCB
from app.handlers._helpers import show_screen
from app.i18n import loc, t
from app.keyboards.inline import parts_keyboard, playall_done_keyboard
from app.services import CatalogService
from app.services.delivery import send_all_chapters

router = Router(name="chapter")
log = logging.getLogger(__name__)

# Strong refs to in-flight background senders so the event loop's GC can't
# cancel a task mid-run (asyncio only holds weak refs to tasks).
_background_tasks: set[asyncio.Task] = set()


async def _deliver_sequence(bot, chat_id, book, chapters, lang, show_part, done_kb) -> None:
    """Background sender: stream the chapter albums, then confirm with a button.
    Errors are logged, never raised as a task error."""
    try:
        sent = await send_all_chapters(bot, chat_id, book, chapters, lang, show_part=show_part)
        await bot.send_message(chat_id, t(lang, "playall_done", n=sent), reply_markup=done_kb)
    except Exception:  # noqa: BLE001
        log.exception("play-all failed (book=%s chat=%s)", book.id, chat_id)
        try:
            await bot.send_message(chat_id, t(lang, "playall_error"))
        except Exception:  # noqa: BLE001
            pass


async def _start_playall(
    callback: CallbackQuery,
    bot: Bot,
    catalog: CatalogService,
    lang: str,
    book,
    section: int,
) -> None:
    """Queue a whole part's audio (in order) and confirm via a background task."""
    chapters = [c for c in await catalog.chapters_of(book.id) if c.section == section]
    ready = [c for c in chapters if c.is_ready]
    if not ready:
        await callback.answer(t(lang, "alert_not_ready"), show_alert=True)
        return

    show_part = len(await catalog.sections_present(book.id)) > 1
    await callback.answer(t(lang, "playall_sending"))  # toast, no chat message
    done_kb = playall_done_keyboard(book.id, lang)
    task = asyncio.create_task(
        _deliver_sequence(
            bot, callback.message.chat.id, book, ready, lang, show_part, done_kb
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@router.callback_query(ChapterCB.filter(F.action == "parts"))
async def list_parts(
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

    sections = await catalog.sections_present(book.id)
    if len(sections) <= 1:  # nothing to choose -> just play it
        await _start_playall(callback, bot, catalog, lang, book, sections[0] if sections else 1)
        return

    text = t(lang, "parts_title", book=escape(loc(book.title, lang)))
    await show_screen(callback, text, parts_keyboard(book, sections, callback_data.page, lang))
    await callback.answer()


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
    await _start_playall(callback, bot, catalog, lang, book, callback_data.section)
