"""Capture Telegram file_id values for local audio/PDF and store them in the DB.

WHY: Telegram lets a bot upload a file ONCE and then re-send it forever, for
free and instantly, by referencing its ``file_id``. So we never store binary
blobs — we upload each file a single time and keep the file_id.

USAGE
-----
1. Make sure the bot can post to a chat, and set MEDIA_CHAT_ID in .env:
     * easiest: open a DM with the bot, press Start, then set MEDIA_CHAT_ID to
       your own Telegram user id; OR
     * create a private channel, add the bot as admin, use the channel id.
2. Lay out files (default root: ./media):

     media/<slug>/cover.jpg          (optional book cover)
     media/<slug>/book.pdf           (optional full PDF; any *.pdf works)
     media/<slug>/01.mp3 ... 15.mp3  (chapters; filename stem = chapter number)
     media/<slug>/meta.json          (optional metadata, see below)

   meta.json (all fields optional; needed to CREATE a brand-new book):
     {
       "title": {"ru": "...", "en": "..."},
       "author": "...",
       "description": {"ru": "...", "en": "..."},
       "sort_order": 1,
       "content_language": "en",
       "chapter_titles": {"1": {"ru": "...", "en": "..."}}
     }

3. Run:  python -m scripts.import_media

Re-running is safe: files present on disk overwrite their stored file_id;
missing files are left untouched.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from aiogram.types import FSInputFile

from app.bot import create_bot
from app.config import settings
from app.db.base import dispose_db, init_db, session_factory
from app.i18n import loc
from app.repositories import BookRepository, ChapterRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("import_media")

AUDIO_EXT = {".mp3", ".m4a", ".m4b", ".ogg", ".oga", ".wav", ".aac", ".flac"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _load_meta(folder: Path) -> dict:
    meta_file = folder / "meta.json"
    if meta_file.exists():
        return json.loads(meta_file.read_text(encoding="utf-8"))
    return {}


async def _import_folder(bot, books, chapters, folder: Path) -> None:
    slug = folder.name
    meta = _load_meta(folder)

    book = await books.get_by_slug(slug)
    if book is None:
        if not meta.get("title"):
            log.warning("Skipping '%s': no DB book and no meta.json title.", slug)
            return
        book = await books.create(
            slug=slug,
            title=meta["title"],
            author=meta.get("author"),
            description=meta.get("description", {}),
            content_language=meta.get("content_language"),
            sort_order=meta.get("sort_order", 0),
            is_published=meta.get("is_published", True),
        )
        log.info("Created book '%s'.", slug)
    elif meta:
        # Refresh metadata from meta.json when present.
        for key in ("title", "author", "description", "sort_order", "content_language"):
            if key in meta:
                setattr(book, key, meta[key])
        await books.update(book)

    chat_id = settings.media_chat_id

    # --- Cover ---
    cover = next((p for p in folder.iterdir() if p.stem.lower() == "cover" and p.suffix.lower() in IMAGE_EXT), None)
    if cover is not None:
        msg = await bot.send_photo(chat_id, photo=FSInputFile(cover))
        book.cover_file_id = msg.photo[-1].file_id
        log.info("[%s] cover -> %s", slug, book.cover_file_id[:16])
        await asyncio.sleep(0.3)

    # --- PDF ---
    pdf = next((p for p in folder.iterdir() if p.suffix.lower() == ".pdf"), None)
    if pdf is not None:
        msg = await bot.send_document(chat_id, document=FSInputFile(pdf))
        book.pdf_file_id = msg.document.file_id
        book.pdf_file_name = msg.document.file_name
        log.info("[%s] pdf -> %s", slug, book.pdf_file_id[:16])
        await asyncio.sleep(0.3)

    await books.update(book)

    # --- Chapters ---
    chapter_titles = meta.get("chapter_titles", {})
    audio_files = sorted(
        (p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXT and p.stem.isdigit()),
        key=lambda p: int(p.stem),
    )
    for audio in audio_files:
        number = int(audio.stem)
        msg = await bot.send_audio(
            chat_id,
            audio=FSInputFile(audio),
            title=str(number),
            performer=loc(book.author, settings.default_language) or settings.brand_name,
        )
        await chapters.upsert(
            book.id,
            number,
            title=chapter_titles.get(str(number), {}),
            audio_file_id=msg.audio.file_id,
            duration=msg.audio.duration,
        )
        log.info("[%s] chapter %s -> %s", slug, number, msg.audio.file_id[:16])
        await asyncio.sleep(0.3)


async def main() -> None:
    if settings.media_chat_id is None:
        raise SystemExit("Set MEDIA_CHAT_ID in .env before importing media.")

    root = Path(settings.media_root)
    if not root.exists():
        raise SystemExit(f"Media root '{root}' does not exist.")

    await init_db()
    bot = create_bot()
    try:
        async with session_factory() as session:
            books = BookRepository(session)
            chapters = ChapterRepository(session)
            for folder in sorted(p for p in root.iterdir() if p.is_dir()):
                await _import_folder(bot, books, chapters, folder)
            await session.commit()
    finally:
        await bot.session.close()
        await dispose_db()
    log.info("Media import complete.")


if __name__ == "__main__":
    asyncio.run(main())
