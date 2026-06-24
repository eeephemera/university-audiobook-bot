"""Typed application configuration, loaded from environment / .env file.

A single ``Settings`` instance (``settings``) is imported across the app.
Everything that an operator might want to change lives here — nothing is
hard-coded deeper in the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    bot_token: str
    # NoDecode: stop pydantic-settings from JSON-decoding the env value so our
    # comma-separated parser (the validator below) receives the raw string.
    admin_ids: Annotated[list[int], NoDecode] = []

    # --- Branding / UX ---
    brand_name: str = "Audiobook Library"
    default_language: str = "ru"
    # Telegram username users can contact for questions / bugs / suggestions.
    support_username: str = "NAGO95"

    # --- Storage ---
    database_url: str = "sqlite+aiosqlite:///data/bot.db"

    # --- Media import (scripts/import_media.py only) ---
    # A chat the bot can post to, used to capture file_id values when uploading
    # local audio/PDF. Your own chat (after /start) or a private channel where
    # the bot is admin. Not used by the running bot itself.
    media_chat_id: int | None = None
    media_root: str = "media"

    # --- Networking ---
    # Optional proxy for reaching api.telegram.org (e.g. when Telegram is blocked).
    # Full URL with scheme: http://user:pass@host:port or socks5://user:pass@host:port
    telegram_proxy: str | None = None

    # --- Behaviour flags ---
    use_rich_messages: bool = False
    protect_content: bool = False
    drop_pending_updates: bool = True

    # --- Logging ---
    log_level: str = "INFO"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        """Allow ADMIN_IDS to be given as a comma-separated string in .env."""
        if isinstance(value, str):
            return [int(p) for p in value.replace(";", ",").split(",") if p.strip()]
        return value

    @field_validator("default_language")
    @classmethod
    def _normalize_lang(cls, value: str) -> str:
        return value.strip().lower()[:2] or "ru"

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
