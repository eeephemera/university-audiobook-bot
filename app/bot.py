"""Compose the Bot + Dispatcher and run long-polling."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from app.config import settings
from app.db.base import dispose_db, init_db
from app.handlers import routers
from app.logging_setup import setup_logging
from app.middlewares import ContextMiddleware

log = logging.getLogger(__name__)

# Commands shown in the Telegram "/" menu. Default scope is English; a Russian
# scope is layered on top.
_COMMANDS = {
    "en": [
        BotCommand(command="start", description="Main menu"),
        BotCommand(command="catalog", description="Books"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="help", description="Help"),
    ],
    "ru": [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="catalog", description="Книги"),
        BotCommand(command="language", description="Сменить язык"),
        BotCommand(command="help", description="Помощь"),
    ],
}


def create_bot() -> Bot:
    # Route Telegram traffic through a proxy when configured (e.g. RF blocking).
    session = AiohttpSession(proxy=settings.telegram_proxy) if settings.telegram_proxy else None
    if session is not None:
        log.info("Using Telegram proxy")
    return Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ContextMiddleware())
    for router in routers:
        dp.include_router(router)
    return dp


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(_COMMANDS["en"], scope=BotCommandScopeDefault())
    await bot.set_my_commands(
        _COMMANDS["ru"], scope=BotCommandScopeDefault(), language_code="ru"
    )


async def run() -> None:
    setup_logging()
    await init_db()

    bot = create_bot()
    dp = create_dispatcher()

    me = await bot.me()
    log.info("Starting @%s (id=%s)", me.username, me.id)

    try:
        await _set_commands(bot)
        await dp.start_polling(
            bot,
            drop_pending_updates=settings.drop_pending_updates,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()
        await dispose_db()
        log.info("Bot stopped.")
