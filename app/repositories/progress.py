"""Progress repository — 'continue listening' bookmarks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int, book_id: int) -> Progress | None:
        stmt = select(Progress).where(
            Progress.user_id == user_id, Progress.book_id == book_id
        )
        return await self.session.scalar(stmt)

    async def set_chapter(
        self, user_id: int, book_id: int, section: int, chapter: int
    ) -> None:
        progress = await self.get(user_id, book_id)
        if progress is None:
            progress = Progress(
                user_id=user_id,
                book_id=book_id,
                last_section=section,
                last_chapter=chapter,
            )
            self.session.add(progress)
        else:
            progress.last_section = section
            progress.last_chapter = chapter
        await self.session.flush()
