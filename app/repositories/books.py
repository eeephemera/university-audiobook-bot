"""Book repository — reads for users, writes reserved for the admin panel."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Book


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Reads (used by the user-facing bot) ---
    async def list_published(self, offset: int = 0, limit: int = 6) -> list[Book]:
        stmt = (
            select(Book)
            .where(Book.is_published.is_(True))
            .order_by(Book.sort_order, Book.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(stmt)).all())

    async def count_published(self) -> int:
        stmt = select(func.count()).select_from(Book).where(Book.is_published.is_(True))
        return int(await self.session.scalar(stmt) or 0)

    async def get(self, book_id: int) -> Book | None:
        return await self.session.get(Book, book_id)

    async def get_by_slug(self, slug: str) -> Book | None:
        stmt = select(Book).where(Book.slug == slug)
        return await self.session.scalar(stmt)

    async def search(self, query: str, limit: int = 12) -> list[Book]:
        """Case-insensitive search over localised titles + author.

        The catalog is small, so we filter in Python — this stays correct
        across SQLite/Postgres without relying on JSON-path SQL dialects.
        """
        needle = query.strip().lower()
        if not needle:
            return []
        stmt = (
            select(Book)
            .where(Book.is_published.is_(True))
            .order_by(Book.sort_order, Book.id)
        )
        results: list[Book] = []
        for book in (await self.session.scalars(stmt)).all():
            haystack = " ".join(
                [*(book.title or {}).values(), *(book.author or {}).values()]
            ).lower()
            if needle in haystack:
                results.append(book)
            if len(results) >= limit:
                break
        return results

    # --- Writes (reserved for the future admin panel / import scripts) ---
    async def create(self, **fields) -> Book:
        book = Book(**fields)
        self.session.add(book)
        await self.session.flush()
        return book

    async def update(self, book: Book, **fields) -> Book:
        for key, value in fields.items():
            setattr(book, key, value)
        await self.session.flush()
        return book

    async def delete(self, book: Book) -> None:
        await self.session.delete(book)
        await self.session.flush()
