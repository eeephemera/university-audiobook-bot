"""Inline mode — share books into any chat via @<bot> <query>.

Each result posts a card whose text carries the signature footer + deep link,
so the sharing loop matches the forward-signature behaviour.
"""

from __future__ import annotations

from html import escape

from aiogram import Bot, Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from app.formatting import with_signature
from app.i18n import loc, t
from app.services import CatalogService

router = Router(name="inline")


@router.inline_query()
async def inline_search(
    query: InlineQuery, bot: Bot, catalog: CatalogService, lang: str
) -> None:
    text = (query.query or "").strip()
    books = await catalog.search(text) if text else (await catalog.page(0))[0]
    me = await bot.me()

    results: list[InlineQueryResultArticle] = []
    for book in books[:20]:
        title = loc(book.title, lang)
        ready = await catalog.ready_count(book.id)
        body = f"📖 <b>{escape(title)}</b>"
        if book.author:
            body += f"\n<i>{escape(book.author)}</i>"
        message_text = with_signature(
            body, lang, me.username, payload=f"book_{book.slug}"
        )
        results.append(
            InlineQueryResultArticle(
                id=str(book.id),
                title=title,
                description=t(lang, "inline_book_description", chapters=ready),
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML",
                ),
            )
        )

    await query.answer(results, cache_time=15, is_personal=True)
