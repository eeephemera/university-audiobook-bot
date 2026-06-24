"""Load a catalog JSON into the database.

Run:  python -m scripts.seed

Picks ``data/catalog.json`` if present (a real export with file_ids, produced by
``scripts/export_catalog.py``), otherwise falls back to ``data/sample_catalog.json``.

Idempotent: books are matched by slug and chapters by (section, number), so
re-running updates rather than duplicates. This is how the bot is provisioned on
a server WITHOUT transferring the binary DB or the media — the file_ids live in
the JSON and are valid for whatever bot token they were uploaded with.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.db.base import dispose_db, init_db, session_factory
from app.repositories import BookRepository, ChapterRepository

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _catalog_path() -> Path:
    real = DATA_DIR / "catalog.json"
    return real if real.exists() else DATA_DIR / "sample_catalog.json"


async def main() -> None:
    await init_db()
    path = _catalog_path()
    payload = json.loads(path.read_text(encoding="utf-8"))

    async with session_factory() as session:
        books = BookRepository(session)
        chapters = ChapterRepository(session)

        for entry in payload["books"]:
            fields = dict(
                title=entry["title"],
                author=entry.get("author"),
                description=entry.get("description", {}),
                content_language=entry.get("content_language"),
                cover_file_id=entry.get("cover_file_id"),
                pdf_file_id=entry.get("pdf_file_id"),
                pdf_file_name=entry.get("pdf_file_name"),
                sections=entry.get("sections", {}),
                is_published=entry.get("is_published", True),
                sort_order=entry.get("sort_order", 0),
            )
            book = await books.get_by_slug(entry["slug"])
            if book is None:
                book = await books.create(slug=entry["slug"], **fields)
            else:
                await books.update(book, **fields)

            for ch in entry.get("chapters", []):
                await chapters.upsert(
                    book.id,
                    ch["number"],
                    section=ch.get("section", 1),
                    title=ch.get("title", {}),
                    audio_file_id=ch.get("audio_file_id"),
                    duration=ch.get("duration"),
                )

        await session.commit()

    await dispose_db()
    print(f"Seed complete from {path.name}: {len(payload['books'])} book(s).")


if __name__ == "__main__":
    asyncio.run(main())
