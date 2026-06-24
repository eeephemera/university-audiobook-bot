"""User repository — upsert on every update, language preference."""

from __future__ import annotations

from aiogram.types import User as TgUser
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
        await self.session.flush()
        return user

    async def set_language(self, user: User, language: str) -> None:
        user.language = normalize(language)
        await self.session.flush()
