"""Router registry.

Order matters: specific handlers first, the free-text search and the catch-all
callback (``common``) last so they only catch what nothing else claimed.
"""

from aiogram import Router

from app.handlers import admin, catalog, chapter, common, inline, search, start

routers: list[Router] = [
    start.router,
    catalog.router,
    chapter.router,
    inline.router,
    admin.router,
    search.router,
    common.router,
]

__all__ = ["routers"]
