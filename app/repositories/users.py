"""User repository — upsert on every update, language preference."""

from __future__ import annotations

from datetime import datetime

from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.i18n import normalize


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_or_create(self, tg_user: TgUser) -> User:
        """Fetch or create the DB user, refreshing volatile profile fields.

        Idempotent under concurrency: if two near-simultaneous updates for a
        brand-new user both try to INSERT, the loser catches the PK conflict,
        rolls back and re-fetches the row the winner created.
        """
        user = await self.session.get(User, tg_user.id)
        if user is None:
            user = User(
                id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language=normalize(tg_user.language_code),
            )
            self.session.add(user)
            try:
                await self.session.flush()
                return user
            except IntegrityError:
                await self.session.rollback()
                user = await self.session.get(User, tg_user.id)
                if user is None:
                    raise

        # Existing row (or the one a concurrent update created): keep profile
        # fields current; never overwrite the user's chosen language.
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        # Force last_seen to bump every interaction (SQLAlchemy skips the UPDATE
        # when only equal values are reassigned, so set it explicitly) — this is
        # what makes "active users" analytics reliable.
        user.last_seen = func.now()
        await self.session.flush()
        return user

    async def set_language(self, user: User, language: str) -> None:
        user.language = normalize(language)
        await self.session.flush()

    # --- Analytics ---
    async def count(self) -> int:
        return int(await self.session.scalar(select(func.count()).select_from(User)) or 0)

    async def count_created_since(self, cutoff: datetime) -> int:
        stmt = select(func.count()).select_from(User).where(User.created_at >= cutoff)
        return int(await self.session.scalar(stmt) or 0)

    async def count_active_since(self, cutoff: datetime) -> int:
        stmt = select(func.count()).select_from(User).where(User.last_seen >= cutoff)
        return int(await self.session.scalar(stmt) or 0)

    async def language_counts(self) -> list[tuple[str, int]]:
        stmt = (
            select(User.language, func.count())
            .group_by(User.language)
            .order_by(func.count().desc())
        )
        return [(lang, int(c)) for lang, c in (await self.session.execute(stmt)).all()]
