"""Resolve a localised content value ({"ru": .., "en": ..}) for a user."""

from __future__ import annotations

from app.config import settings
from app.i18n.engine import normalize


def loc(value: dict[str, str] | str | None, lang: str | None) -> str:
    """Pick the best available translation of a DB content field.

    Order: requested language -> default language -> any non-empty value.
    Accepts a plain string too (returned as-is) for forgiving call sites.
    """
    if isinstance(value, str):
        return value
    if not value:
        return ""

    code = normalize(lang)
    if value.get(code):
        return value[code]

    default = settings.default_language
    if value.get(default):
        return value[default]

    for candidate in value.values():
        if candidate:
            return candidate
    return ""
