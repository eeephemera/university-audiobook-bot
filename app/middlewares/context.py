"""Per-update context middleware.

Opens ONE database session per update, upserts the calling user, resolves their
language, and injects everything handlers need:

    data["session"]  -> AsyncSession
    data["catalog"]  -> CatalogService bound to that session
    data["user"]     -> DB User (or None for service updates)
    data["lang"]     -> resolved UI language code

The session is committed if the handler succeeds and rolled back on error, so
handlers never manage transactions themselves.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TgUser

from app.config import settings
from app.db.base import session_factory
from app.repositories import UserRepository
from app.services import CatalogService

log = logging.getLogger(__name__)


class ContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with session_factory() as session:
            data["session"] = session
            data["catalog"] = CatalogService(session)
            tg_user: TgUser | None = data.get("event_from_user")

            try:
                # Inside the try so a flush failure here also rolls back.
                user = None
                lang = settings.default_language
                if tg_user is not None and not tg_user.is_bot:
                    user = await UserRepository(session).get_or_create(tg_user)
                    lang = user.language
                data["user"] = user
                data["lang"] = lang

                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
