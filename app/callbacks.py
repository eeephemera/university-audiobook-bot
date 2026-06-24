"""Typed callback-data factories (aiogram CallbackData).

Centralised so buttons and handlers share one source of truth for the wire
format of every inline button.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="m"):
    action: str  # home | catalog | about | language | search


class CatalogCB(CallbackData, prefix="cat"):
    page: int = 0


class BookCB(CallbackData, prefix="b"):
    action: str  # open | chapters | pdf
    book_id: int
    page: int = 0  # catalog page to return to


class ChapterCB(CallbackData, prefix="ch"):
    action: str  # parts | list | play
    book_id: int
    section: int = 1
    number: int = 0
    page: int = 0  # catalog page to return to


class LangCB(CallbackData, prefix="lng"):
    code: str  # ru | en
