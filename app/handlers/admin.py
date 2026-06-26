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

from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.repositories import UserRepository

router = Router(name="admin")

# Every handler in this router is restricted to configured ADMIN_IDS.
router.message.filter(IsAdmin())


@router.message(Command("admin"))
async def admin_home(message: Message) -> None:
    await message.answer(
        "🛠 <b>Admin panel</b>\n\n"
        "• <b>/stats</b> — статистика пользователей ✅\n\n"
        "<i>В разработке (архитектура готова):</i>\n"
        "<blockquote>"
        "• <b>/addbook</b> — мастер добавления книги\n"
        "• прислать PDF / аудио для привязки (file_id ловится автоматически)\n"
        "• <b>/publish</b> — показать/скрыть книгу\n"
        "• <b>/reorder</b> — порядок в каталоге"
        "</blockquote>"
    )


@router.message(Command("stats"))
async def stats(message: Message, session: AsyncSession) -> None:
    users = UserRepository(session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # match SQLite UTC

    total = await users.count()
    active_24h = await users.count_active_since(now - timedelta(days=1))
    active_7d = await users.count_active_since(now - timedelta(days=7))
    new_24h = await users.count_created_since(now - timedelta(days=1))
    new_7d = await users.count_created_since(now - timedelta(days=7))
    new_30d = await users.count_created_since(now - timedelta(days=30))
    langs = await users.language_counts()
    lang_line = " · ".join(f"{lang}: {c}" for lang, c in langs) or "—"

    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n\n"
        f"🟢 Активные\n"
        f"   за 24ч: <b>{active_24h}</b> · за 7д: <b>{active_7d}</b>\n\n"
        f"🆕 Новые\n"
        f"   24ч: <b>{new_24h}</b> · 7д: <b>{new_7d}</b> · 30д: <b>{new_30d}</b>\n\n"
        f"🌐 Языки: {lang_line}"
    )
