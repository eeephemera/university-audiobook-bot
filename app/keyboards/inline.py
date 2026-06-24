"""Inline keyboard builders. All user-visible text comes from i18n."""

from __future__ import annotations

import math

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import BookCB, CatalogCB, ChapterCB, LangCB, MenuCB
from app.db.models import Book
from app.i18n import SUPPORTED, loc, t

# How many books per catalog page.
CATALOG_PAGE_SIZE = 6

_NOOP = "noop"  # non-actionable buttons (e.g. the page counter)
_LANG_LABELS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}


def main_menu(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "menu_catalog"), callback_data=MenuCB(action="catalog"))
    kb.button(text=t(lang, "menu_search"), callback_data=MenuCB(action="search"))
    kb.button(text=t(lang, "menu_about"), callback_data=MenuCB(action="about"))
    kb.button(text=t(lang, "menu_language"), callback_data=MenuCB(action="language"))
    kb.adjust(1, 2)
    return kb.as_markup()


def catalog_keyboard(
    books: list[Book], page: int, total: int, lang: str
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        kb.button(
            text=f"📖 {loc(book.title, lang)}",
            callback_data=BookCB(action="open", book_id=book.id, page=page),
        )
    kb.adjust(1)

    pages = max(1, math.ceil(total / CATALOG_PAGE_SIZE))
    if pages > 1:
        nav = InlineKeyboardBuilder()
        if page > 0:
            nav.button(text="◀️", callback_data=CatalogCB(page=page - 1))
        nav.button(text=f"{page + 1}/{pages}", callback_data=_NOOP)
        if page < pages - 1:
            nav.button(text="▶️", callback_data=CatalogCB(page=page + 1))
        nav.adjust(3)
        kb.attach(nav)

    home = InlineKeyboardBuilder()
    home.button(text=t(lang, "menu_home"), callback_data=MenuCB(action="home"))
    kb.attach(home)
    return kb.as_markup()


def book_keyboard(
    book: Book,
    page: int,
    *,
    ready_count: int,
    sections: list[int],
    lang: str,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if ready_count > 0:
        if len(sections) > 1:
            # Multi-part: pick a part first.
            listen_cb = ChapterCB(action="parts", book_id=book.id, page=page)
        else:
            # Single part: play it straight away.
            only = sections[0] if sections else 1
            listen_cb = ChapterCB(
                action="playall", book_id=book.id, section=only, page=page
            )
        kb.button(text=t(lang, "btn_chapters"), callback_data=listen_cb)
    if book.has_pdf:
        kb.button(
            text=t(lang, "btn_pdf"),
            callback_data=BookCB(action="pdf", book_id=book.id, page=page),
        )
    kb.button(text=t(lang, "btn_back"), callback_data=CatalogCB(page=page))
    kb.adjust(1)
    return kb.as_markup()


def parts_keyboard(
    book: Book, sections: list[int], page: int, lang: str
) -> InlineKeyboardMarkup:
    """One button per part; tapping plays that whole part straight away."""
    kb = InlineKeyboardBuilder()
    titles = book.sections or {}
    for sec in sections:
        title = loc(titles.get(str(sec)), lang)
        label = f"📚 {t(lang, 'lbl_part')} {sec}"
        if title:
            label += f" — {title}"
        kb.button(
            text=label,
            callback_data=ChapterCB(action="playall", book_id=book.id, section=sec, page=page),
        )
    kb.button(
        text=t(lang, "btn_back"),
        callback_data=BookCB(action="open", book_id=book.id, page=page),
    )
    kb.adjust(1)
    return kb.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code in SUPPORTED:
        kb.button(text=_LANG_LABELS.get(code, code), callback_data=LangCB(code=code))
    kb.adjust(2)
    return kb.as_markup()


def only_home(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "menu_home"), callback_data=MenuCB(action="home"))
    return kb.as_markup()


def playall_done_keyboard(book_id: int, lang: str) -> InlineKeyboardMarkup:
    """Buttons under the 'play-all done' message: choose a part, or go home.

    'parts' opens the part-selection screen for multi-part books, and falls back
    to the chapter list for flat (single-part) books.
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t(lang, "btn_choose_part"),
        callback_data=ChapterCB(action="parts", book_id=book_id),
    )
    kb.button(text=t(lang, "menu_home"), callback_data=MenuCB(action="home"))
    kb.adjust(1)
    return kb.as_markup()


def search_results_keyboard(books: list[Book], lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        kb.button(
            text=f"📖 {loc(book.title, lang)}",
            callback_data=BookCB(action="open", book_id=book.id, page=0),
        )
    kb.button(text=t(lang, "menu_home"), callback_data=MenuCB(action="home"))
    kb.adjust(1)
    return kb.as_markup()
