"""Entry points: /start (+ deep links), /help, main-menu navigation, language."""

from __future__ import annotations

from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from app.callbacks import LangCB, MenuCB
from app.config import settings
from app.handlers._helpers import show_screen
from app.i18n import t
from app.keyboards.inline import language_keyboard, main_menu, only_home
from app.services import CatalogService
from app.views import book_card

router = Router(name="start")


def _welcome_text(lang: str) -> str:
    return t(lang, "welcome", brand=escape(settings.brand_name))


async def _send_book_card(
    message: Message,
    bot: Bot,
    catalog: CatalogService,
    book,
    lang: str,
) -> None:
    me = await bot.me()
    ready = await catalog.ready_count(book.id)
    sections = await catalog.sections_present(book.id)
    text, kb = book_card(book, ready, sections, 0, lang, me.username)
    if book.cover_file_id:
        await message.answer_photo(book.cover_file_id, caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(CommandStart(deep_link=True))
async def start_deeplink(
    message: Message,
    command: CommandObject,
    bot: Bot,
    catalog: CatalogService,
    lang: str,
) -> None:
    """Handle t.me/<bot>?start=book_<slug> — open the shared book directly."""
    payload = command.args or ""
    if payload.startswith("book_"):
        book = await catalog.get_book_by_slug(payload[len("book_"):])
        if book and book.is_published:
            await _send_book_card(message, bot, catalog, book, lang)
            return
    await message.answer(_welcome_text(lang), reply_markup=main_menu(lang))


@router.message(CommandStart())
async def start(message: Message, lang: str) -> None:
    await message.answer(_welcome_text(lang), reply_markup=main_menu(lang))


@router.message(Command("help"))
async def help_cmd(message: Message, bot: Bot, lang: str) -> None:
    me = await bot.me()
    await message.answer(t(lang, "help", bot=me.username), reply_markup=main_menu(lang))


@router.callback_query(MenuCB.filter(F.action == "home"))
async def go_home(callback: CallbackQuery, lang: str) -> None:
    await show_screen(callback, _welcome_text(lang), main_menu(lang))
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "about"))
async def about(callback: CallbackQuery, lang: str) -> None:
    text = t(lang, "about", brand=escape(settings.brand_name))
    await show_screen(callback, text, only_home(lang))
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "language"))
async def choose_language(callback: CallbackQuery, lang: str) -> None:
    await show_screen(callback, t(lang, "language_choose"), language_keyboard())
    await callback.answer()


@router.callback_query(LangCB.filter())
async def set_language(
    callback: CallbackQuery,
    callback_data: LangCB,
    catalog: CatalogService,
    user,
) -> None:
    new_lang = callback_data.code
    if user is not None:
        await catalog.set_language(user, new_lang)
    await show_screen(callback, _welcome_text(new_lang), main_menu(new_lang))
    await callback.answer(t(new_lang, "language_set"))
