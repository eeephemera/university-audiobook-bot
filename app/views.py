"""Pure presentation helpers: build screen text + keyboard, no I/O.

Handlers call these and decide whether to ``edit_text`` or ``answer``.
"""

from __future__ import annotations

from html import escape

from aiogram.types import InlineKeyboardMarkup

from app.db.models import Book
from app.formatting import with_signature
from app.i18n import loc, t
from app.keyboards.inline import book_keyboard

# The card doubles as a photo caption when the book has a cover, so keep the
# whole thing comfortably under Telegram's 1024-char caption limit.
_MAX_TITLE = 120
_MAX_AUTHOR = 80
_MAX_DESCRIPTION = 500


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def book_card(
    book: Book,
    ready_count: int,
    bookmark: tuple[int, int] | None,
    sections: list[int],
    page: int,
    lang: str,
    bot_username: str,
) -> tuple[str, InlineKeyboardMarkup]:
    """Render a book's detail card (rich text) + its action keyboard.

    The signature footer is included so a forwarded card still points home.
    """
    parts = [f"📖 <b>{escape(_clip(loc(book.title, lang), _MAX_TITLE))}</b>"]
    author = loc(book.author, lang)
    if author:
        parts.append(f"<i>{t(lang, 'lbl_author')}: {escape(_clip(author, _MAX_AUTHOR))}</i>")

    description = loc(book.description, lang)
    if description:
        # Plain (non-collapsing) blockquote so the synopsis is readable at once.
        parts.append(f"\n<blockquote>{escape(_clip(description, _MAX_DESCRIPTION))}</blockquote>")

    if ready_count == 0:
        parts.append(f"\n{t(lang, 'coming_soon')}")

    text = with_signature(
        "\n".join(parts), lang, bot_username, payload=f"book_{book.slug}"
    )
    keyboard = book_keyboard(
        book, page, ready_count=ready_count, bookmark=bookmark,
        sections=sections, lang=lang,
    )
    return text, keyboard
