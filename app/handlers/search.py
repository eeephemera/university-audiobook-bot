"""Search. The 'Search' button shows a prompt; any free text runs a search.

No FSM state is needed — treating plain text as a query is simpler and means a
student can just type a title from anywhere.
"""

from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.callbacks import MenuCB
from app.handlers._helpers import show_screen
from app.i18n import t
from app.keyboards.inline import only_home, search_results_keyboard
from app.services import CatalogService

router = Router(name="search")


@router.callback_query(MenuCB.filter(F.action == "search"))
async def search_prompt(callback: CallbackQuery, lang: str) -> None:
    await show_screen(callback, t(lang, "search_prompt"), only_home(lang))
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def search_text(message: Message, catalog: CatalogService, lang: str) -> None:
    query = (message.text or "").strip()
    books = await catalog.search(query)
    if not books:
        await message.answer(
            t(lang, "search_no_results", query=escape(query)),
            reply_markup=only_home(lang),
        )
        return
    await message.answer(
        t(lang, "search_results_title", query=escape(query)),
        reply_markup=search_results_keyboard(books, lang),
    )
