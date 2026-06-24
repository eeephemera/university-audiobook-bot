"""SQLAlchemy models.

Design notes for the FUTURE ADMIN PANEL (not built yet, but the schema is
ready for it):

* Localised text (``title``, ``description``) is stored as a JSON map
  ``{"ru": "...", "en": "..."}``. Adding a language is a data change, not a
  migration. Resolve it with ``app.i18n.localized.loc``.
* Every catalog row carries ``is_published`` + ``sort_order`` so an admin can
  stage content and reorder it without deleting anything.
* Audio/PDF are stored as Telegram ``file_id`` strings, NOT as blobs. A file is
  uploaded to Telegram exactly once (see ``scripts/import_media.py``); after
  that every user is served instantly and for free by re-sending the file_id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# A localised string: {"ru": "...", "en": "..."}.
LocalizedText = dict[str, str]


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Stable human-readable id used in deep links (t.me/bot?start=book_<slug>).
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    title: Mapped[LocalizedText] = mapped_column(JSON, default=dict)
    author: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    description: Mapped[LocalizedText] = mapped_column(JSON, default=dict)

    cover_file_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    pdf_file_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    pdf_file_name: Mapped[Optional[str]] = mapped_column(String(255), default=None)

    # Optional part/section titles, keyed by section number as a string:
    #   {"1": {"ru": "О том, что предшествовало Ашуре", "en": "..."}, "2": {...}}
    # Empty => the book is a flat list of chapters (no part-selection screen).
    sections: Mapped[dict] = mapped_column(JSON, default=dict)

    # Informational: the language the audio/PDF themselves are in.
    content_language: Mapped[Optional[str]] = mapped_column(String(8), default=None)

    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # lazy="raise": chapters are ALWAYS read through ChapterRepository, never via
    # this relationship — so accidental ORM access fails loudly instead of
    # firing a hidden per-Book bulk query on hot paths (catalog/search/inline).
    # passive_deletes relies on the DB's ON DELETE CASCADE (SQLite FK pragma is
    # enabled in db/base.py) for the future admin delete flow.
    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="Chapter.number",
        lazy="raise",
        passive_deletes=True,
    )

    @property
    def has_pdf(self) -> bool:
        return bool(self.pdf_file_id)


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("book_id", "section", "number", name="uq_book_chapter"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True
    )
    # Part/section number (1 for flat books). Global order is (section, number).
    section: Mapped[int] = mapped_column(Integer, default=1)
    number: Mapped[int] = mapped_column(Integer)  # chapter number within its part

    title: Mapped[LocalizedText] = mapped_column(JSON, default=dict)
    audio_file_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    duration: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # seconds
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, default=None)  # bytes

    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    book: Mapped["Book"] = relationship(back_populates="chapters")

    @property
    def is_ready(self) -> bool:
        """A chapter is playable once its audio has been uploaded."""
        return bool(self.audio_file_id) and self.is_published


class User(Base):
    """A bot user. Stored for language preference, analytics and (later) admin."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    username: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    language: Mapped[str] = mapped_column(String(8), default="ru")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Progress(Base):
    """Last listened chapter per (user, book) — powers 'Continue listening'."""

    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True
    )
    # Bookmark position. last_section pairs with last_chapter for paged books.
    last_section: Mapped[int] = mapped_column(Integer, default=1)
    last_chapter: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
