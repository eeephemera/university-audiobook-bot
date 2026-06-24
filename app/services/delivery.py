"""Delivery of the actual artefacts (audio chapters, PDFs).

Every caption is finished with the signature footer (see formatting/rich.py),
so when a student forwards a chapter or PDF, the recipient sees which bot it
came from plus a deep link back in.
"""

from __future__ import annotations

import asyncio
from html import escape
from itertools import groupby

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

# Bound the unbounded (JSON) fields so the assembled caption + footer always
# stays well under Telegram's 1024-char caption limit. We clip the RAW text
# before escaping/wrapping, so HTML tags and entities are never cut mid-way.
_MAX_TITLE = 200
_MAX_AUTHOR = 120
_MAX_CH_TITLE = 200


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _pdf_caption(book: Book, lang: str) -> str:
    title = escape(_clip(loc(book.title, lang), _MAX_TITLE))
    lines = [f"📄 <b>{title}</b>", f"<i>{t(lang, 'lbl_pdf_version')}</i>"]
    if book.author:
        lines.insert(1, f"<i>{t(lang, 'lbl_author')}: {escape(_clip(book.author, _MAX_AUTHOR))}</i>")
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


def _range_label(group: list[Chapter], lang: str) -> str:
    a, b = group[0].number, group[-1].number
    if a == b:
        return f"{t(lang, 'lbl_chapter')} {a}"
    return f"{t(lang, 'lbl_chapters')} {a}–{b}"


def _album_caption(
    book: Book,
    group: list[Chapter],
    lang: str,
    *,
    show_part: bool,
    with_footer: bool,
    bot_username: str,
) -> str:
    """Каждый альбом подписан: часть (если есть) + диапазон глав внутри него."""
    rng = _range_label(group, lang)
    if show_part:
        sec = group[0].section
        head = f"📚 <b>{t(lang, 'lbl_part')} {sec}</b>"
        part_title = loc((book.sections or {}).get(str(sec)), lang)
        if part_title:
            head += f" · {escape(_clip(part_title, _MAX_TITLE))}"
        caption = f"{head}\n🎧 {rng}"
    else:
        title = escape(_clip(loc(book.title, lang), _MAX_TITLE))
        caption = f"🎧 <b>{title}</b>\n📖 {rng}"

    if with_footer:
        caption = caption_with_signature(
            caption, lang, bot_username, payload=f"book_{book.slug}"
        )
    return caption


async def send_all_chapters(
    bot: Bot,
    chat_id: int,
    book: Book,
    chapters: list[Chapter],
    lang: str,
    *,
    show_part: bool = False,
) -> int:
    """Send chapters as audio albums, in order, so Telegram auto-advances.

    Albums never cross a part boundary (group by section, then chunk by 10), and
    each album's first track is captioned with its part + chapter range. The
    brand/link footer rides on the very first album only.
    """
    me = await bot.me()
    performer = (book.author or settings.brand_name)[:_META_LIMIT]

    def track_title(ch: Chapter) -> str:
        title = loc(ch.title, lang)
        if title:
            return _clip(title, _META_LIMIT)
        return f"{ch.section}.{ch.number}" if show_part else str(ch.number)

    albums: list[list[Chapter]] = []
    for _sec, items in groupby(chapters, key=lambda c: c.section):
        part = list(items)
        for i in range(0, len(part), _GROUP_SIZE):
            albums.append(part[i : i + _GROUP_SIZE])

    sent = 0
    for index, group in enumerate(albums):
        # The label goes in its OWN text message ABOVE the audios — a media-group
        # caption renders between the 1st and 2nd track, which reads out of order.
        header = _album_caption(
            book, group, lang,
            show_part=show_part, with_footer=(index == 0), bot_username=me.username,
        )
        await _send_with_retry(
            lambda h=header: bot.send_message(chat_id, h, parse_mode=ParseMode.HTML)
        )
        if len(group) == 1:
            # Media groups require >= 2 items; send a lone track solo.
            ch = group[0]
            await _send_with_retry(
                lambda ch=ch: bot.send_audio(
                    chat_id,
                    audio=ch.audio_file_id,
                    title=track_title(ch),
                    performer=performer,
                    protect_content=settings.protect_content,
                )
            )
        else:
            media = [
                InputMediaAudio(
                    media=ch.audio_file_id,
                    title=track_title(ch),
                    performer=performer,
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
