"""Data-access layer.

Repositories are the ONLY place that talks to the ORM. Handlers and services go
through them, which keeps SQL in one layer and makes the future admin panel a
matter of calling the already-existing ``create`` / ``update`` / ``delete``
methods rather than touching the database directly.
"""

from app.repositories.books import BookRepository
from app.repositories.chapters import ChapterRepository
from app.repositories.progress import ProgressRepository
from app.repositories.users import UserRepository

__all__ = [
    "BookRepository",
    "ChapterRepository",
    "UserRepository",
    "ProgressRepository",
]
