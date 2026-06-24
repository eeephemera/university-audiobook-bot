"""Chapter repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter


class ChapterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_book(self, book_id: int) -> list[Chapter]:
        """All chapters in global reading order (section, then number)."""
        stmt = (
            select(Chapter)
            .where(Chapter.book_id == book_id)
            .order_by(Chapter.section, Chapter.number)
        )
        return list((await self.session.scalars(stmt)).all())

    async def get(self, book_id: int, section: int, number: int) -> Chapter | None:
        stmt = select(Chapter).where(
            Chapter.book_id == book_id,
            Chapter.section == section,
            Chapter.number == number,
        )
        return await self.session.scalar(stmt)

    async def count_ready(self, book_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Chapter)
            .where(
                Chapter.book_id == book_id,
                Chapter.is_published.is_(True),
                Chapter.audio_file_id.is_not(None),
            )
        )
        return int(await self.session.scalar(stmt) or 0)

    # --- Writes (import scripts / future admin panel) ---
    async def upsert(
        self, book_id: int, number: int, section: int = 1, **fields
    ) -> Chapter:
        chapter = await self.get(book_id, section, number)
        if chapter is None:
            chapter = Chapter(
                book_id=book_id, section=section, number=number, **fields
            )
            self.session.add(chapter)
        else:
            for key, value in fields.items():
                setattr(chapter, key, value)
        await self.session.flush()
        return chapter
