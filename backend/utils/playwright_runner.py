"""Run Playwright off the server event loop on Windows.

Uvicorn's reload worker uses a selector event loop. That loop cannot start
the subprocess Playwright needs, so every scraper fails immediately.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def run_on_playwright_loop(factory: Callable[[], Awaitable[T]]) -> T:
    """Await factory() on a loop that can launch browser processes."""
    if sys.platform != "win32":
        return await factory()

    running = asyncio.get_running_loop()

    def _in_thread() -> T:
        loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(factory())
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    return await running.run_in_executor(None, _in_thread)
