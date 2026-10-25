"""
YouTube Data API lookup for one intro, one deep-dive, and one project video.

The API key stays on the server. Missing key, quota errors, and empty filter
results become a YouTube search link for that stage. Those links are not cached.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote_plus

import httpx

from config import settings
from database import fetch_all, insert_row, update_row
from services.reading_resources import subject_for_skill
from utils.youtube_rank import (
    STAGES,
    VideoCandidate,
    candidates_from_videos_list,
    choose_videos,
    format_duration,
)

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_CACHE_TTL = timedelta(days=30)
_TIMEOUT = 12.0

_STAGE_QUERIES = {
    "intro": "{skill} for beginners crash course",
    "deep_dive": "{skill} in depth tutorial explained",
    "project": "{skill} project build from scratch tutorial",
}
_JAPANESE_QUERIES = {
    "intro": "JLPT {level} grammar lesson for beginners",
    "deep_dive": "JLPT {level} grammar in depth explained",
    "project": "JLPT {level} reading and listening practice lesson",
}


def stage_query(skill: str) -> dict[str, str]:
    """Search text for each stage. Japanese skills use the JLPT level."""
    _key, level = subject_for_skill(skill)
    if level:
        return {stage: template.format(level=level) for stage, template in _JAPANESE_QUERIES.items()}
    return {stage: template.format(skill=skill) for stage, template in _STAGE_QUERIES.items()}


def search_link(stage: str, query: str) -> dict:
    """A real YouTube search URL. This is not a made-up video."""
    return {
        "kind": "search_link",
        "stage": stage,
        "videoId": None,
        "title": f"Search YouTube: {query}",
        "channel": None,
        "duration": None,
        "views": None,
        "publishedAt": None,
        "thumbnail": None,
        "url": f"https://www.youtube.com/results?search_query={quote_plus(query)}",
    }


def video_payload(video: VideoCandidate, stage: str) -> dict:
    published = video.published_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "kind": "video",
        "stage": stage,
        "videoId": video.video_id,
        "title": video.title,
        "channel": video.channel,
        "duration": format_duration(video.duration_seconds),
        "views": video.views,
        "publishedAt": published,
        "thumbnail": video.thumbnail or None,
        "url": f"https://www.youtube.com/watch?v={video.video_id}",
    }


def _cache_skill_key(skill: str) -> str:
    key, level = subject_for_skill(skill)
    if key == "japanese" and level:
        return f"japanese:{level.lower()}"
    return key or skill.strip().lower()


def _parse_time(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_cache(skill_key: str, stage: str, now: datetime) -> Optional[dict]:
    try:
        rows = fetch_all("learning_video_cache", filters={"skill_key": skill_key, "stage": stage})
    except Exception:
        logger.warning("YouTube cache is unavailable for %s/%s", skill_key, stage, exc_info=True)
        return None
    if not rows:
        return None
    row = rows[0]
    fetched = _parse_time(row.get("fetched_at"))
    payload = row.get("payload")
    if not fetched or not isinstance(payload, dict):
        return None
    if now - fetched > _CACHE_TTL:
        return None
    if payload.get("kind") != "video":
        return None
    return payload


def _write_cache(skill_key: str, stage: str, payload: dict) -> None:
    try:
        rows = fetch_all("learning_video_cache", filters={"skill_key": skill_key, "stage": stage})
        if rows:
            update_row("learning_video_cache", str(rows[0]["id"]), {"payload": payload, "fetched_at": datetime.now(timezone.utc).isoformat()})
        else:
            insert_row(
                "learning_video_cache",
                {"skill_key": skill_key, "stage": stage, "payload": payload},
            )
    except Exception:
        logger.warning("Could not store YouTube cache for %s/%s", skill_key, stage, exc_info=True)


def _get(url: str, params: dict) -> dict:
    response = httpx.get(url, params=params, timeout=_TIMEOUT)
    if response.status_code == 403:
        logger.warning("YouTube API refused the request (quota or permission)")
        return {}
    if response.status_code >= 400:
        logger.warning("YouTube API error %s", response.status_code)
        return {}
    data = response.json()
    if data.get("error"):
        logger.warning("YouTube API error: %s", data["error"].get("message", "unknown"))
        return {}
    return data


def _search_ids(query: str, api_key: str, language: str) -> list[str]:
    data = _get(
        _SEARCH_URL,
        {
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "safeSearch": "moderate",
            "maxResults": 10,
            "q": query,
            "relevanceLanguage": language,
            "key": api_key,
        },
    )
    ids: list[str] = []
    for item in data.get("items") or []:
        video_id = ((item.get("id") or {}).get("videoId")) or ""
        if video_id and video_id not in ids:
            ids.append(video_id)
    return ids


def _fetch_candidates(video_ids: list[str], api_key: str) -> list[VideoCandidate]:
    if not video_ids:
        return []
    data = _get(
        _VIDEOS_URL,
        {
            "part": "snippet,contentDetails,statistics,status",
            "id": ",".join(video_ids[:50]),
            "key": api_key,
        },
    )
    return candidates_from_videos_list(data)


def videos_for_skill(skill: str, api_key: Optional[str] = None, now: Optional[datetime] = None) -> list[dict]:
    """
    Three results, one per stage. Real videos come from the API. Otherwise a search link.
    """
    moment = now or datetime.now(timezone.utc)
    queries = stage_query(skill)
    key = (api_key if api_key is not None else settings.youtube_api_key).strip()
    skill_key, level = subject_for_skill(skill)
    cache_key = _cache_skill_key(skill)
    catalog_key = "japanese" if level else skill_key

    results: list[dict] = []
    missing_stages: list[str] = []
    already_used: set[str] = set()
    for stage in STAGES:
        cached = _read_cache(cache_key, stage, moment)
        if cached:
            results.append(cached)
            if cached.get("videoId"):
                already_used.add(cached["videoId"])
        else:
            missing_stages.append(stage)

    if not missing_stages:
        return results

    if not key:
        logger.info("YOUTUBE_API_KEY is not set — returning search links")
        for stage in missing_stages:
            results.append(search_link(stage, queries[stage]))
        return _ordered(results)

    languages = ("en", "ja") if level else ("en",)
    by_stage: dict[str, list[VideoCandidate]] = {}
    try:
        for stage in missing_stages:
            ids: list[str] = []
            for language in languages:
                for video_id in _search_ids(queries[stage], key, language):
                    if video_id not in ids:
                        ids.append(video_id)
            by_stage[stage] = _fetch_candidates(ids, key)
    except httpx.HTTPError:
        logger.warning("YouTube request failed", exc_info=True)
        by_stage = {}

    chosen = choose_videos(by_stage, skill, catalog_key, moment, excluded_ids=already_used)
    for stage in missing_stages:
        video = chosen.get(stage)
        if video is None:
            results.append(search_link(stage, queries[stage]))
            continue
        payload = video_payload(video, stage)
        _write_cache(cache_key, stage, payload)
        results.append(payload)
    return _ordered(results)


def _ordered(items: list[dict]) -> list[dict]:
    by_stage = {item.get("stage"): item for item in items}
    return [by_stage[stage] for stage in STAGES if stage in by_stage]
