"""Request every curated reading URL and report anything that is not HTTP 200."""

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "backend" / "data" / "skill_resources.json"


def _urls(node) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        if isinstance(node.get("url"), str):
            found.append(node["url"])
        for value in node.values():
            found.extend(_urls(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_urls(item))
    return found


def _status(url: str) -> str:
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JobAnalyzerLinkCheck/1.0)"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return str(response.status)
    except HTTPError as exc:
        return str(exc.code)
    except URLError as exc:
        return f"error: {exc.reason}"


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    urls = list(dict.fromkeys(_urls(catalog)))
    failures: list[tuple[str, str]] = []
    for url in urls:
        status = _status(url)
        if status != "200":
            failures.append((status, url))
            print(f"FAIL {status} {url}")
        else:
            print(f"OK   {status} {url}")
    print(f"\n{len(urls) - len(failures)} ok, {len(failures)} failed, {len(urls)} checked")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
