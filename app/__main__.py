"""Run with:  python -m app"""

from __future__ import annotations

import asyncio
import contextlib

from app.bot import run


def main() -> None:
    # uvloop speeds up the event loop on Linux VPS; absent/unsupported on Windows.
    with contextlib.suppress(ImportError):
        import uvloop

        uvloop.install()

    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
