"""Delivery of the actual artefacts (audio chapters, PDFs).

Every caption is finished with the signature footer (see formatting/rich.py),
so when a student forwards a chapter or PDF, the recipient sees which bot it
came from plus a deep link back in.
"""

from __future__ import annotations

import asyncio
from html import escape

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InputMediaAudio, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import BookCB
from app.config import settings
from app.db.models import Book, Chapter
from app.formatting import caption_with_signature
from app.i18n import loc, t
from app.keyboards.inline import chapter_nav_keyboard

# Bound the unbounded (JSON) fields so the assembled caption + footer always
# stays well under Telegram's 1024-char caption limit. We clip the RAW text
# before escaping/wrapping, so HTML tags and entities are never cut mid-way.
_MAX_TITLE = 200
_MAX_AUTHOR = 120
_MAX_CH_TITLE = 200


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _chapter_caption(
    book: Book, chapter: Chapter, lang: str, *, show_part: bool, part_title: str
) -> str:
    title = escape(_clip(loc(book.title, lang), _MAX_TITLE))
    lines = [f"🎧 <b>{title}</b>"]
    author = loc(book.author, lang)
    if author:
        lines.append(f"<i>{t(lang, 'lbl_author')}: {escape(_clip(author, _MAX_AUTHOR))}</i>")
    if show_part:
        pl = f"<i>{t(lang, 'lbl_part')} {chapter.section}"
        if part_title:
            pl += f": {escape(_clip(part_title, _MAX_TITLE))}"
        pl += "</i>"
        lines.append(pl)
    line = f"📖 <b>{t(lang, 'lbl_chapter')} {chapter.number}</b>"
    ch_title = loc(chapter.title, lang)
    if ch_title:
        line += f" — {escape(_clip(ch_title, _MAX_CH_TITLE))}"
    lines.append(line)
    return "\n".join(lines)


async def send_chapter(
    bot: Bot,
    chat_id: int,
    book: Book,
    chapter: Chapter,
    lang: str,
    *,
    ordered_ready: list[tuple[int, int]],
    show_part: bool = False,
    part_title: str = "",
) -> Message:
    """Send one chapter as audio, with prev/next nav (reliable sequential play)."""
    me = await bot.me()
    caption = _chapter_caption(book, chapter, lang, show_part=show_part, part_title=part_title)
    caption = caption_with_signature(caption, lang, me.username, payload=f"book_{book.slug}")
    nav = chapter_nav_keyboard(book.id, (chapter.section, chapter.number), ordered_ready, lang)
    return await bot.send_audio(
        chat_id,
        audio=chapter.audio_file_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=nav,
        protect_content=settings.protect_content,
    )


def _pdf_caption(book: Book, lang: str) -> str:
    title = escape(_clip(loc(book.title, lang), _MAX_TITLE))
    lines = [f"📄 <b>{title}</b>", f"<i>{t(lang, 'lbl_pdf_version')}</i>"]
    author = loc(book.author, lang)
    if author:
        lines.insert(1, f"<i>{t(lang, 'lbl_author')}: {escape(_clip(author, _MAX_AUTHOR))}</i>")
    return "\n".join(lines)


# Audio is delivered as media-group "albums" (up to 10 tracks each) so a whole
# book lands as a few compact grouped blocks instead of dozens of bubbles —
# while Telegram's player still auto-advances across them.
_GROUP_SIZE = 10
_GROUP_PACE = 1.0
_META_LIMIT = 64  # Telegram title/performer length cap


async def _send_with_retry(make_coro):
    """Run a send, waiting out a single TelegramRetryAfter (flood limit)."""
    for attempt in range(2):
        try:
            return await make_coro()
        except TelegramRetryAfter as exc:
            if attempt == 0:
                await asyncio.sleep(exc.retry_after + 1)
                continue
            raise


def _entry_caption(book: Book, lang: str, bot_username: str) -> str:
    """Caption for the entry track (chapter 1) — book title + brand footer."""
    title = escape(_clip(loc(book.title, lang), _MAX_TITLE))
    return caption_with_signature(
        f"🎧 <b>{title}</b>", lang, bot_username, payload=f"book_{book.slug}"
    )


async def send_all_chapters(
    bot: Bot,
    chat_id: int,
    book: Book,
    chapters: list[Chapter],
    lang: str,
    *,
    show_part: bool = False,
) -> int:
    """Send all chapters as compact audio albums so they auto-play in order.

    Telegram's player auto-advances to the ADJACENT message; on phones it goes
    upward (the dominant client here). So we send in REVERSE: chapter 1 ends up
    at the BOTTOM (sent last), and tapping it plays upward 1 → N. The brand
    footer rides on that entry track. (On desktop the player goes downward, so
    there the order is mirrored — there is no single send order correct for both
    clients; this favours mobile.)
    """
    if not chapters:
        return 0
    me = await bot.me()
    performer = (loc(book.author, lang) or settings.brand_name)[:_META_LIMIT]

    def track_title(ch: Chapter) -> str:
        title = loc(ch.title, lang)
        if title:
            return _clip(title, _META_LIMIT)
        return f"{ch.section}.{ch.number}" if show_part else str(ch.number)

    entry = chapters[0]                 # chapter 1 — the tap point
    seq = list(reversed(chapters))      # send N..1 so the bottom message is ch.1

    sent = 0
    for start in range(0, len(seq), _GROUP_SIZE):
        group = seq[start : start + _GROUP_SIZE]
        if len(group) == 1:
            ch = group[0]
            cap = _entry_caption(book, lang, me.username) if ch is entry else None
            await _send_with_retry(
                lambda ch=ch, cap=cap: bot.send_audio(
                    chat_id, audio=ch.audio_file_id, title=track_title(ch),
                    performer=performer, caption=cap, parse_mode=ParseMode.HTML,
                    protect_content=settings.protect_content,
                )
            )
        else:
            media = [
                InputMediaAudio(
                    media=ch.audio_file_id,
                    title=track_title(ch),
                    performer=performer,
                    caption=(_entry_caption(book, lang, me.username) if ch is entry else None),
                    parse_mode=ParseMode.HTML,
                )
                for ch in group
            ]
            await _send_with_retry(
                lambda media=media: bot.send_media_group(
                    chat_id, media=media, protect_content=settings.protect_content
                )
            )
        sent += len(group)
        await asyncio.sleep(_GROUP_PACE)
    return sent


async def send_pdf(bot: Bot, chat_id: int, book: Book, lang: str, page: int = 0) -> Message:
    me = await bot.me()
    caption = _pdf_caption(book, lang)
    caption = caption_with_signature(
        caption, lang, me.username, payload=f"book_{book.slug}"
    )
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t(lang, "btn_back"),
        callback_data=BookCB(action="open", book_id=book.id, page=page),
    )
    return await bot.send_document(
        chat_id,
        document=book.pdf_file_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.as_markup(),
        protect_content=settings.protect_content,
    )
