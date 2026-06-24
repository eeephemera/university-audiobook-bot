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


def book_card(
    book: Book,
    ready_count: int,
    sections: list[int],
    page: int,
    lang: str,
    bot_username: str,
) -> tuple[str, InlineKeyboardMarkup]:
    """Render a book's detail card (rich text) + its action keyboard.

    The signature footer is included so a forwarded card still points home.
    """
    parts = [f"📖 <b>{escape(loc(book.title, lang))}</b>"]
    if book.author:
        parts.append(f"<i>{t(lang, 'lbl_author')}: {escape(book.author)}</i>")

    description = loc(book.description, lang)
    if description:
        # Plain (non-collapsing) blockquote so the synopsis is readable at once.
        parts.append(f"\n<blockquote>{escape(description)}</blockquote>")

    if ready_count == 0:
        parts.append(f"\n{t(lang, 'coming_soon')}")

    text = with_signature(
        "\n".join(parts), lang, bot_username, payload=f"book_{book.slug}"
    )
    keyboard = book_keyboard(
        book, page, ready_count=ready_count, sections=sections, lang=lang
    )
    return text, keyboard
