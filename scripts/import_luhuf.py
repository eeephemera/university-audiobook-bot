"""Importer for the first book — «Лухуф. Скорби Кербелы» (Сейид Ибн Тавус).

The audio is organised in 3 parts (parts/sections), with files named like:
    "1. 1. Рождение Хусейна_1.mp3"
    "1.3. Двенадцать ангелов.mp3"
    "2.1 Войско для сражения с Хусейном. mp3.mp3"   (note the doubled extension)
    "1. 2. Сон Умму ль-Фазль.wav"
This script parses section/number/title out of those names.

USAGE
-----
* DRY RUN (no MEDIA_CHAT_ID set): prints the parsed plan and does nothing else —
  use it to sanity-check parsing.
      python -m scripts.import_luhuf
* REAL IMPORT (MEDIA_CHAT_ID set in .env to a chat the bot can post to):
  uploads cover + PDF + every chapter once, captures each file_id, and writes
  the book, its part titles and chapters to the DB.
      python -m scripts.import_luhuf
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path

# Windows consoles default to cp1251 and choke on Cyrillic in print()/logging.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:  # pragma: no cover
        pass

from aiogram.types import FSInputFile

from app.bot import create_bot
from app.config import settings
from app.db.base import dispose_db, init_db, session_factory
from app.repositories import BookRepository, ChapterRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("import_luhuf")

BOOK_DIR = Path(__file__).resolve().parents[1] / "ЛУХУФ. СКОРБИ КЕРБЕЛЫ"
COVER_FILE = "photo_1_2026-06-24_12-46-47.jpg"
PDF_FILE = "Лухуф.pdf"

BOOK = {
    "slug": "luhuf-skorbi-kerbely",
    "title": {"ru": "Лухуф. Скорби Кербелы", "en": "Al-Luhuf: The Sorrows of Karbala"},
    "author": "Сейид Ибн Тавус",
    "description": {
        "ru": (
            "«Ал-Лухуф ‘аля катля ат-туфуф» Сейида Ибн Тавуса — классическое "
            "повествование о трагедии Кербелы и мученичестве Имама Хусейна "
            "(мир ему): предыстория, события дня Ашуры и то, что произошло "
            "после. Аудиоверсия в трёх частях и полный PDF."
        ),
        "en": (
            "Sayyid Ibn Tawus's classic account of the tragedy of Karbala and "
            "the martyrdom of Imam Husayn (peace be upon him): the events "
            "leading up to Ashura, the day itself, and the aftermath. Audio in "
            "three parts plus the full PDF."
        ),
    },
    "content_language": "ru",
    "sort_order": 1,
    "sections": {
        "1": {"ru": "О том, что предшествовало Ашуре", "en": "Before Ashura"},
        "2": {"ru": "О сражении Кербелы", "en": "The Battle of Karbala"},
        "3": {"ru": "О событиях после Кербелы", "en": "After Karbala"},
    },
}

# Strip one or more trailing ".mp3"/".wav"/" mp3" (handles doubled extensions).
_EXT = re.compile(r"(?:\s*\.?\s*(?:mp3|wav))+\s*$", re.IGNORECASE)
# Leading "<section>.<number>." with flexible spacing/dots.
_HEAD = re.compile(r"^\s*(\d+)\s*\.\s*(\d+)\s*\.?\s*(.*)$", re.DOTALL)
_AUDIO_SUFFIXES = (".mp3", ".wav")


def parse_filename(name: str) -> tuple[int, int, str] | None:
    """('1.3. Двенадцать ангелов.mp3') -> (1, 3, 'Двенадцать ангелов')."""
    stem = _EXT.sub("", name).strip()
    m = _HEAD.match(stem)
    if not m:
        return None
    section, number = int(m.group(1)), int(m.group(2))
    title = re.sub(r"_\d+$", "", m.group(3).strip()).strip(" .")
    return section, number, title


def collect() -> list[tuple[int, int, str, Path]]:
    items: list[tuple[int, int, str, Path]] = []
    for path in BOOK_DIR.iterdir():
        if path.suffix.lower() not in _AUDIO_SUFFIXES:
            continue
        parsed = parse_filename(path.name)
        if parsed is None:
            log.warning("Could not parse, skipping: %s", path.name)
            continue
        section, number, title = parsed
        items.append((section, number, title, path))
    items.sort(key=lambda x: (x[0], x[1]))
    return items


def _print_plan(items: list[tuple[int, int, str, Path]]) -> None:
    by_section: dict[int, int] = {}
    for section, _n, _t, _p in items:
        by_section[section] = by_section.get(section, 0) + 1
    print(f"\nBook: {BOOK['title']['ru']} — {BOOK['author']}")
    print(f"Folder: {BOOK_DIR}")
    print(f"Cover present: {(BOOK_DIR / COVER_FILE).exists()} | "
          f"PDF present: {(BOOK_DIR / PDF_FILE).exists()}")
    print(f"Total audio chapters: {len(items)}")
    for section in sorted(by_section):
        title = BOOK["sections"].get(str(section), {}).get("ru", "")
        print(f"\n  Часть {section}: {title}  ({by_section[section]} глав)")
        for s, n, t, _p in items:
            if s == section:
                print(f"    {s}.{n:<3} {t}")


async def _import(items: list[tuple[int, int, str, Path]]) -> None:
    chat_id = settings.media_chat_id
    bot = create_bot()
    await init_db()
    try:
        async with session_factory() as session:
            books = BookRepository(session)
            chapters = ChapterRepository(session)

            book = await books.get_by_slug(BOOK["slug"])
            fields = {k: v for k, v in BOOK.items() if k != "slug"}
            if book is None:
                book = await books.create(slug=BOOK["slug"], **fields)
            else:
                await books.update(book, **fields)

            cover = BOOK_DIR / COVER_FILE
            if cover.exists():
                msg = await bot.send_photo(chat_id, photo=FSInputFile(cover))
                book.cover_file_id = msg.photo[-1].file_id
                log.info("cover -> %s", book.cover_file_id[:16])
                await asyncio.sleep(0.3)

            pdf = BOOK_DIR / PDF_FILE
            if pdf.exists():
                msg = await bot.send_document(chat_id, document=FSInputFile(pdf))
                book.pdf_file_id = msg.document.file_id
                book.pdf_file_name = msg.document.file_name
                log.info("pdf -> %s", book.pdf_file_id[:16])
                await asyncio.sleep(0.3)

            await books.update(book)

            failures: list[tuple[int, int, str, str]] = []
            ok = 0
            for section, number, title, path in items:
                try:
                    msg = await bot.send_audio(
                        chat_id,
                        audio=FSInputFile(path),
                        title=title or f"{section}.{number}",
                        performer=BOOK["author"],
                    )
                    await chapters.upsert(
                        book.id,
                        number,
                        section=section,
                        title={"ru": title} if title else {},
                        audio_file_id=msg.audio.file_id,
                        duration=msg.audio.duration,
                    )
                    ok += 1
                    log.info("%s.%s -> %s", section, number, msg.audio.file_id[:16])
                except Exception as exc:  # noqa: BLE001 - one bad file shouldn't abort
                    log.warning("FAILED %s.%s (%s): %s", section, number, path.name, exc)
                    failures.append((section, number, path.name, str(exc)))
                await asyncio.sleep(0.3)

            await session.commit()
    finally:
        await bot.session.close()
        await dispose_db()

    log.info("Done: %s ok, %s failed (of %s).", ok, len(failures), len(items))
    if failures:
        print("\nThe following chapters were NOT imported (re-run after fixing):")
        for section, number, name, err in failures:
            print(f"  {section}.{number}  {name}\n      {err}")


async def main() -> None:
    if not BOOK_DIR.exists():
        raise SystemExit(f"Folder not found: {BOOK_DIR}")
    items = collect()

    if settings.media_chat_id is None:
        print("\n=== DRY RUN (MEDIA_CHAT_ID is not set — nothing uploaded) ===")
        _print_plan(items)
        print("\nSet MEDIA_CHAT_ID in .env, then re-run to upload & import.")
        return

    await _import(items)


if __name__ == "__main__":
    asyncio.run(main())
