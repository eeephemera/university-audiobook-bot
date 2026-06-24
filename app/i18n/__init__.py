"""Internationalisation.

UI strings live in plain dicts (``ru.py`` / ``en.py``) resolved by
``engine.t``. Catalog content (book titles, descriptions) is localised
separately via ``localized.loc`` because it lives in the database.

Adding a language = add a ``xx.py`` dict and register it in ``engine.py``.
"""

from app.i18n.engine import SUPPORTED, normalize, t
from app.i18n.localized import loc

__all__ = ["t", "loc", "normalize", "SUPPORTED"]
