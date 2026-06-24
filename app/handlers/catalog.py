"""Catalog browsing: list, pagination, book card, PDF delivery."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.callbacks import BookCB, CatalogCB, MenuCB
from app.handlers._helpers import show_photo_screen, show_screen
from app.i18n import t
from app.keyboards.inline import catalog_keyboard, only_home
from app.services import CatalogService
from app.services.delivery import send_pdf
from app.views import book_card

router = Router(name="catalog")


async def _catalog_view(catalog: CatalogService, lang: str, page: int):
    books, total = await catalog.page(page)
    if not books:
        return t(lang, "catalog_empty"), only_home(lang)
    return t(lang, "catalog_title"), catalog_keyboard(books, page, total, lang)


@router.message(Command("catalog"))
async def catalog_cmd(message: Message, catalog: CatalogService, lang: str) -> None:
    text, kb = await _catalog_view(catalog, lang, 0)
    await message.answer(text, reply_markup=kb)


@router.callback_query(MenuCB.filter(F.action == "catalog"))
async def catalog_menu(callback: CallbackQuery, catalog: CatalogService, lang: str) -> None:
    text, kb = await _catalog_view(catalog, lang, 0)
    await show_screen(callback, text, kb)
    await callback.answer()


@router.callback_query(CatalogCB.filter())
async def catalog_page(
    callback: CallbackQuery, callback_data: CatalogCB, catalog: CatalogService, lang: str
) -> None:
    text, kb = await _catalog_view(catalog, lang, callback_data.page)
    await show_screen(callback, text, kb)
    await callback.answer()


@router.callback_query(BookCB.filter(F.action == "open"))
async def open_book(
    callback: CallbackQuery,
    callback_data: BookCB,
    bot: Bot,
    catalog: CatalogService,
    lang: str,
) -> None:
    book = await catalog.get_book(callback_data.book_id)
    if book is None or not book.is_published:
        await callback.answer(t(lang, "alert_not_found"), show_alert=True)
        return
    me = await bot.me()
    ready = await catalog.ready_count(book.id)
    sections = await catalog.sections_present(book.id)
    text, kb = book_card(book, ready, sections, callback_data.page, lang, me.username)
    if book.cover_file_id:
        await show_photo_screen(callback, book.cover_file_id, text, kb)
    else:
        await show_screen(callback, text, kb)
    await callback.answer()


@router.callback_query(BookCB.filter(F.action == "pdf"))
async def book_pdf(
    callback: CallbackQuery,
    callback_data: BookCB,
    bot: Bot,
    catalog: CatalogService,
    lang: str,
) -> None:
    book = await catalog.get_book(callback_data.book_id)
    if book is None:
        await callback.answer(t(lang, "alert_not_found"), show_alert=True)
        return
    if not book.has_pdf:
        await callback.answer(t(lang, "alert_no_pdf"), show_alert=True)
        return
    await send_pdf(bot, callback.message.chat.id, book, lang, callback_data.page)
    await callback.answer()
