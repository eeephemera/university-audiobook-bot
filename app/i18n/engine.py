"""Tiny dict-based translation engine (no heavy i18n dependency)."""

from __future__ import annotations

from app.config import settings
from app.i18n.en import EN
from app.i18n.ru import RU

TRANSLATIONS: dict[str, dict[str, str]] = {"ru": RU, "en": EN}
SUPPORTED: tuple[str, ...] = tuple(TRANSLATIONS.keys())


def normalize(code: str | None) -> str:
    """Map any Telegram language_code to a supported UI language."""
    if not code:
        return settings.default_language
    short = code.lower().replace("_", "-").split("-", 1)[0]
    return short if short in TRANSLATIONS else settings.default_language


def t(lang: str | None, key: str, /, **kwargs: object) -> str:
    """Translate ``key`` into ``lang`` with ``str.format`` substitution.

    Falls back to the default language, then to the key itself, so a missing
    string degrades visibly instead of crashing.
    """
    table = TRANSLATIONS.get(normalize(lang), TRANSLATIONS[settings.default_language])
    template = table.get(key)
    if template is None:
        template = TRANSLATIONS[settings.default_language].get(key, key)
    return template.format(**kwargs) if kwargs else template
