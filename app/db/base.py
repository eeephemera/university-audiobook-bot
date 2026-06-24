"""Database engine, session factory and schema bootstrap.

We keep the data-access stack deliberately thin and swappable:

    engine  ->  async_sessionmaker  ->  AsyncSession  ->  repositories

The middleware (``app/middlewares/db.py``) opens one session per update and
hands it to the repositories, so handlers never touch the engine directly.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base shared by every model."""


engine = create_async_engine(settings.database_url, echo=False, future=True)

# SQLite does not enforce foreign keys (or ON DELETE CASCADE) unless asked, per
# connection. Turn it on so the passive-delete cascade on Book.chapters works.
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


def _ensure_sqlite_dir() -> None:
    """Create the parent folder for a file-based SQLite DB if missing."""
    url = settings.database_url
    if url.startswith("sqlite") and ":///" in url:
        db_path = url.split(":///", 1)[1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


async def init_db() -> None:
    """Create tables if they do not exist.

    For real schema migrations (the admin panel will add columns over time)
    introduce Alembic — ``create_all`` only creates what is missing.
    """
    # Import models so they register on Base.metadata before create_all.
    from app.db import models  # noqa: F401

    _ensure_sqlite_dir()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database ready: %s", settings.database_url)


async def dispose_db() -> None:
    await engine.dispose()
