"""Business logic over the repositories.

Handlers depend on this service, not on raw repositories — so paging rules,
'continue listening' logic, etc. live in one place and the future admin panel
reuses the same methods.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Book, Chapter, User
from app.keyboards.inline import CATALOG_PAGE_SIZE
from app.repositories import (
    BookRepository,
    ChapterRepository,
    ProgressRepository,
    UserRepository,
)


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.books = BookRepository(session)
        self.chapters = ChapterRepository(session)
        self.users = UserRepository(session)
        self.progress = ProgressRepository(session)

    # --- Catalog browsing ---
    async def page(self, page: int) -> tuple[list[Book], int]:
        total = await self.books.count_published()
        books = await self.books.list_published(page * CATALOG_PAGE_SIZE, CATALOG_PAGE_SIZE)
        return books, total

    async def get_book(self, book_id: int) -> Book | None:
        return await self.books.get(book_id)

    async def get_book_by_slug(self, slug: str) -> Book | None:
        return await self.books.get_by_slug(slug)

    async def search(self, query: str) -> list[Book]:
        return await self.books.search(query)

    # --- Chapters ---
    async def chapters_of(self, book_id: int) -> list[Chapter]:
        """All chapters in global reading order (section, number)."""
        return await self.chapters.list_for_book(book_id)

    async def chapters_in_section(self, book_id: int, section: int) -> list[Chapter]:
        chapters = await self.chapters.list_for_book(book_id)
        return [c for c in chapters if c.section == section]

    async def sections_present(self, book_id: int) -> list[int]:
        """Distinct section numbers that actually have chapters, in order."""
        chapters = await self.chapters.list_for_book(book_id)
        seen: list[int] = []
        for c in chapters:
            if c.section not in seen:
                seen.append(c.section)
        return seen

    async def get_chapter(
        self, book_id: int, section: int, number: int
    ) -> Chapter | None:
        return await self.chapters.get(book_id, section, number)

    async def ready_count(self, book_id: int) -> int:
        return await self.chapters.count_ready(book_id)

    # --- Progress ('continue listening') ---
    async def bookmark(self, user_id: int, book_id: int) -> tuple[int, int] | None:
        """The (section, chapter) the user last listened to, or None."""
        progress = await self.progress.get(user_id, book_id)
        return (progress.last_section, progress.last_chapter) if progress else None

    async def listened(self, user_id: int, book_id: int) -> set[tuple[int, int]]:
        """(section, number) pairs heard so far — up to and incl. the bookmark."""
        mark = await self.bookmark(user_id, book_id)
        if mark is None:
            return set()
        chapters = await self.chapters.list_for_book(book_id)
        result: set[tuple[int, int]] = set()
        for c in chapters:
            if (c.section, c.number) <= mark:
                result.add((c.section, c.number))
        return result

    async def save_progress(
        self, user_id: int, book_id: int, section: int, number: int
    ) -> None:
        await self.progress.set_chapter(user_id, book_id, section, number)

    # --- Preferences ---
    async def set_language(self, user: User, code: str) -> None:
        await self.users.set_language(user, code)
