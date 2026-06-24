"""Admin panel — SCAFFOLD ONLY (intentionally not implemented yet).

The customer asked us to *design the architecture* for self-service content
management but to defer building it. Everything below is the seam it will plug
into; the data layer (repositories + services) already exposes the CRUD methods
an admin panel needs, so building it later is mostly handlers + FSM wizards.

Planned flows (no code yet):
  /admin                     -> dashboard (counts, last uploads)
  /addbook                   -> FSM wizard: slug -> title(ru/en) -> author ->
                                description -> cover photo -> done
  send a PDF while editing   -> capture document.file_id -> BookRepository.update
  send an audio while editing-> capture audio.file_id     -> ChapterRepository.upsert
  /publish <slug>            -> toggle Book.is_published
  /reorder                   -> set sort_order

Implementation notes for later:
  * Uploading a file to the bot returns a `file_id`; store THAT (never re-upload).
    See scripts/import_media.py for the same capture pattern done from the CLI.
  * Gate write actions with the IsAdmin filter (already applied to this router).
  * Add an FSM storage capable of surviving restarts (Redis) before relying on
    multi-step wizards in production.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.filters import IsAdmin

router = Router(name="admin")

# Every handler in this router is restricted to configured ADMIN_IDS.
router.message.filter(IsAdmin())


@router.message(Command("admin"))
async def admin_home(message: Message) -> None:
    await message.answer(
        "🛠 <b>Admin panel</b>\n\n"
        "<i>Reserved — not implemented in this version.</i>\n\n"
        "<blockquote>Planned (architecture is already in place):\n"
        "• <b>/addbook</b> — step-by-step book wizard\n"
        "• send a PDF / audio to attach it (file_id captured automatically)\n"
        "• <b>/publish</b> — show or hide a book\n"
        "• <b>/reorder</b> — change catalog order\n\n"
        "The data layer already supports all of this; only the UI is pending."
        "</blockquote>"
    )
