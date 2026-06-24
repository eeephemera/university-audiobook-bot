"""Centralised logging configuration."""

from __future__ import annotations

import logging

from app.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # aiogram is chatty at INFO for every update; keep our logs readable.
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
