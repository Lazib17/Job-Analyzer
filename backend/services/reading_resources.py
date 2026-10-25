"""Curated reading links. Unknown skills get a search link, never a guessed URL."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from utils.learning_rank import canonical_skill

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "skill_resources.json"
_JAPANESE_TARGET = re.compile(r"japanese\s*\(target\s*(n[1-5]|native)\)", re.IGNORECASE)
_JLPT = re.compile(r"\bjlpt\s*(n[1-5])\b", re.IGNORECASE)


@lru_cache
def _catalog() -> dict:
    with _DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def subject_for_skill(skill: str) -> tuple[str, str | None]:
    """Return (catalog key, JLPT level or None)."""
    match = _JAPANESE_TARGET.search(skill or "")
    if match:
        level = match.group(1)
        return "japanese", "Native" if level.lower() == "native" else level.upper()

    jlpt = _JLPT.search(skill or "")
    if jlpt:
        return "japanese", jlpt.group(1).upper()

    key = canonical_skill(skill)
    if key in {"japanese", "jlpt"} or key.startswith("japanese ") or key.startswith("jlpt "):
        return "japanese", None
    return key, None


def _clean_entry(entry: dict) -> dict | None:
    title = (entry.get("title") or "").strip()
    url = (entry.get("url") or "").strip()
    if not title or not url.startswith("https://"):
        return None
    return {
        "kind": "resource",
        "title": title,
        "url": url,
        "source": entry.get("source") or "",
        "type": entry.get("type") or "docs",
        "difficulty": entry.get("difficulty") or "beginner",
        "estimated_minutes": int(entry.get("estimated_minutes") or 30),
    }


def readings_for_skill(skill: str) -> list[dict]:
    """Return 2–4 curated readings, or one Google search link when nothing is curated."""
    catalog = _catalog()
    key, level = subject_for_skill(skill)
    raw: list[dict] = []

    if key == "japanese":
        japanese = catalog.get("japanese") or {}
        if level and isinstance(japanese.get(level), list):
            raw = japanese[level]
        elif isinstance(japanese.get("N5"), list):
            raw = japanese["N5"]
    else:
        found = catalog.get(key)
        if isinstance(found, list):
            raw = found

    readings = [item for item in (_clean_entry(entry) for entry in raw) if item]
    if readings:
        return readings[:4]

    query = quote_plus(f"{skill} official documentation")
    return [
        {
            "kind": "search_link",
            "title": f"Search for {skill} documentation",
            "url": f"https://www.google.com/search?q={query}",
            "source": "Google",
            "type": "search",
            "difficulty": None,
            "estimated_minutes": None,
        }
    ]
