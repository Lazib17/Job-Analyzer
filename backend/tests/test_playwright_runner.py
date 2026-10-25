import asyncio
import sys

import pytest

from utils.playwright_runner import run_on_playwright_loop


@pytest.mark.skipif(sys.platform != "win32", reason="selector loop only blocks subprocesses on Windows")
def test_runner_starts_a_subprocess_from_a_selector_loop():
    async def child():
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            "print('ok')",
            stdout=asyncio.subprocess.PIPE,
        )
        output, _ = await process.communicate()
        return output.decode().strip()

    async def outer():
        return await run_on_playwright_loop(child)

    loop = asyncio.WindowsSelectorEventLoopPolicy().new_event_loop()
    try:
        assert loop.run_until_complete(outer()) == "ok"
    finally:
        loop.close()
