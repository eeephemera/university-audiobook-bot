"""Export the current DB catalog to data/catalog.json.

This makes the catalog portable WITHOUT shipping the binary SQLite file or the
(large) media: it writes book metadata, part titles and every chapter's
``file_id``. Re-provision anywhere with ``python -m scripts.seed``.

Note: file_ids are bound to the BOT TOKEN that uploaded them, not to a machine —
so the export is only valid for that same bot. It contains NO token and NO user
data, so it is safe to commit.

Run:  python -m scripts.export_catalog
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.db.base import dispose_db, session_factory
from app.repositories import BookRepository, ChapterRepository

OUT = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


async def main() -> None:
    async with session_factory() as session:
        books = BookRepository(session)
        chapters = ChapterRepository(session)

        all_books = await books.list_published(0, 1000)
        payload = {"books": []}
        for book in all_books:
            chs = await chapters.list_for_book(book.id)
            payload["books"].append(
                {
                    "slug": book.slug,
                    "title": book.title,
                    "author": book.author,
                    "description": book.description,
                    "content_language": book.content_language,
                    "sort_order": book.sort_order,
                    "is_published": book.is_published,
                    "sections": book.sections,
                    "cover_file_id": book.cover_file_id,
                    "pdf_file_id": book.pdf_file_id,
                    "pdf_file_name": book.pdf_file_name,
                    "chapters": [
                        {
                            "section": c.section,
                            "number": c.number,
                            "title": c.title,
                            "audio_file_id": c.audio_file_id,
                            "duration": c.duration,
                        }
                        for c in chs
                    ],
                }
            )

    await dispose_db()
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    total_ch = sum(len(b["chapters"]) for b in payload["books"])
    print(f"Exported {len(payload['books'])} book(s), {total_ch} chapter(s) -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
