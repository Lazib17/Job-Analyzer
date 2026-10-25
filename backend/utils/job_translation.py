"""Turn a job page into English or Japanese without changing the saved record."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

_CACHE: dict[tuple[str, str], dict] = {}
_CACHE_LIMIT = 200

_TEXT_FIELDS = (
    "job_title",
    "company",
    "location",
    "salary",
    "description",
    "requirements",
    "ai_reasoning",
    "improvement_suggestions",
)
_LIST_FIELDS = ("matching_skills", "missing_skills")


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.split("\n") if part.strip()]
    return []


def page_payload(job: dict, analysis: Optional[dict]) -> dict:
    """Fields a reader sees on the job page."""
    analysis = analysis or {}
    payload = {field: _text(job.get(field)) for field in _TEXT_FIELDS if field not in _LIST_FIELDS}
    payload["ai_reasoning"] = _text(analysis.get("ai_reasoning"))
    payload["improvement_suggestions"] = _text(analysis.get("improvement_suggestions"))
    payload["matching_skills"] = _list(analysis.get("matching_skills"))
    payload["missing_skills"] = _list(analysis.get("missing_skills"))
    return payload


def payload_has_text(payload: dict) -> bool:
    if any(payload.get(field) for field in _TEXT_FIELDS):
        return True
    return any(payload.get(field) for field in _LIST_FIELDS)


def merge_translation(source: dict, translated: dict) -> dict:
    """Keep the original value whenever the model drops or empties a field."""
    merged = {}
    for field in _TEXT_FIELDS:
        incoming = translated.get(field) if isinstance(translated, dict) else None
        text = _text(incoming)
        merged[field] = text or source.get(field) or ""
    for field in _LIST_FIELDS:
        incoming = translated.get(field) if isinstance(translated, dict) else None
        items = _list(incoming)
        merged[field] = items or list(source.get(field) or [])
    return merged


def cache_key(payload: dict, language: str) -> tuple[str, str]:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return language, digest


def cached_translation(payload: dict, language: str) -> Optional[dict]:
    return _CACHE.get(cache_key(payload, language))


def store_translation(payload: dict, language: str, translated: dict) -> None:
    if len(_CACHE) >= _CACHE_LIMIT:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[cache_key(payload, language)] = translated
