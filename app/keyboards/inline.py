"""Inline keyboard builders. All user-visible text comes from i18n."""

from __future__ import annotations

import math

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks import BookCB, CatalogCB, ChapterCB, LangCB, MenuCB
from app.db.models import Book, Chapter
from app.i18n import SUPPORTED, loc, t

# How many books per catalog page.
CATALOG_PAGE_SIZE = 6
# Chapter-number buttons per row in the chapters grid.
CHAPTERS_PER_ROW = 5

_NOOP = "noop"  # non-actionable buttons (page counter, part headers, locked)
_LANG_LABELS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "fa": "🇮🇷 فارسی"}


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
    bookmark: tuple[int, int] | None,
    sections: list[int],
    lang: str,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if ready_count > 0:
        kb.button(
            text=t(lang, "btn_chapters"),
            callback_data=ChapterCB(action="list", book_id=book.id, page=page),
        )
        if bookmark:
            sec, num = bookmark
            label = f"{sec}.{num}" if len(sections) > 1 else str(num)
            kb.button(
                text=t(lang, "btn_continue", n=label),
                callback_data=ChapterCB(
                    action="play", book_id=book.id, section=sec, number=num, page=page
                ),
            )
    if book.has_pdf:
        kb.button(
            text=t(lang, "btn_pdf"),
            callback_data=BookCB(action="pdf", book_id=book.id, page=page),
        )
    kb.button(text=t(lang, "btn_back"), callback_data=CatalogCB(page=page))
    kb.adjust(1)
    return kb.as_markup()


def chapters_overview_keyboard(
    book: Book,
    chapters: list[Chapter],
    listened: set[tuple[int, int]],
    page: int,
    lang: str,
) -> InlineKeyboardMarkup:
    """All chapters on ONE screen, grouped by part:

        ▶️ Play the whole book
        📚 Part 1 — ...            (header)
        [1][2][3][4][5] ...        (chapter buttons)
        📚 Part 2 — ...
        [1][2][3] ...
        ⬅️ Back
    """
    kb = InlineKeyboardBuilder()
    multi = len({c.section for c in chapters}) > 1

    if any(c.is_ready for c in chapters):
        kb.row(
            InlineKeyboardButton(
                text=t(lang, "btn_play_all_book"),
                callback_data=ChapterCB(action="playall", book_id=book.id, section=0, page=page).pack(),
            )
        )

    titles = book.sections or {}
    order: list[int] = []
    for c in chapters:
        if c.section not in order:
            order.append(c.section)

    for sec in order:
        if multi:
            header = f"📚 {t(lang, 'lbl_part')} {sec}"
            ptitle = loc(titles.get(str(sec)), lang)
            if ptitle:
                header += f" — {ptitle}"
            kb.row(InlineKeyboardButton(text=header, callback_data=_NOOP))

        row: list[InlineKeyboardButton] = []
        for c in (x for x in chapters if x.section == sec):
            if not c.is_ready:
                label, cb = f"🔒 {c.number}", _NOOP
            else:
                mark = "✅ " if (c.section, c.number) in listened else ""
                label = f"{mark}{c.number}"
                cb = ChapterCB(
                    action="play", book_id=book.id, section=c.section,
                    number=c.number, page=page,
                ).pack()
            row.append(InlineKeyboardButton(text=label, callback_data=cb))
            if len(row) == CHAPTERS_PER_ROW:
                kb.row(*row)
                row = []
        if row:
            kb.row(*row)

    kb.row(
        InlineKeyboardButton(
            text=t(lang, "btn_back"),
            callback_data=BookCB(action="open", book_id=book.id, page=page).pack(),
        )
    )
    return kb.as_markup()


def chapter_nav_keyboard(
    book_id: int,
    current: tuple[int, int],
    ordered_ready: list[tuple[int, int]],
    lang: str,
) -> InlineKeyboardMarkup:
    """Prev / chapter-list / next under a sent audio chapter.

    Prev/Next step to the adjacent *ready* chapter in global (section, number)
    order — reliable sequential listening on every Telegram client.
    """
    prev_c = max((c for c in ordered_ready if c < current), default=None)
    next_c = min((c for c in ordered_ready if c > current), default=None)

    kb = InlineKeyboardBuilder()
    if prev_c is not None:
        kb.button(
            text=t(lang, "btn_prev"),
            callback_data=ChapterCB(
                action="play", book_id=book_id, section=prev_c[0], number=prev_c[1]
            ),
        )
    kb.button(
        text=t(lang, "btn_to_chapters"),
        callback_data=ChapterCB(action="list", book_id=book_id),
    )
    if next_c is not None:
        kb.button(
            text=t(lang, "btn_next"),
            callback_data=ChapterCB(
                action="play", book_id=book_id, section=next_c[0], number=next_c[1]
            ),
        )
    kb.adjust(3)
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
    """Buttons under the 'play-all done' message: back to the chapter grid, or home."""
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t(lang, "btn_chapters"),
        callback_data=ChapterCB(action="list", book_id=book_id),
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
