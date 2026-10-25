"""
Pick one YouTube video per learning stage.

Scoring and filtering are pure functions so tests can pass mocked API data.
No network calls live here.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

STAGES = ("intro", "deep_dive", "project")

# Duration window and ideal length, in seconds.
STAGE_WINDOWS = {
    "intro": (5 * 60, 60 * 60, 20 * 60),
    "deep_dive": (20 * 60, 180 * 60, 60 * 60),
    "project": (20 * 60, 240 * 60, 90 * 60),
}

# Skills whose good lessons stay useful for a long time.
FUNDAMENTALS = {
    "javascript",
    "python",
    "sql",
    "postgresql",
    "git",
    "html",
    "css",
    "java",
    "c",
    "c++",
    "c#",
    "go",
    "japanese",
}

FAST_MOVING_YEARS = 5
FUNDAMENTAL_YEARS = 12
MIN_VIEWS = 1000
MIN_VIEWS_JAPANESE = 300

_CLICKBAIT = re.compile(
    r"you won'?t believe|shocking|insane|gone wrong|must watch|\$\$\$|100% guaranteed",
    re.IGNORECASE,
)
_DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


@dataclass
class VideoCandidate:
    video_id: str
    title: str
    channel: str
    duration_seconds: int
    views: int
    likes: int
    published_at: datetime
    embeddable: bool
    thumbnail: str


def parse_iso8601_duration(value: str) -> int:
    """Convert a YouTube duration such as PT1H2M3S into seconds."""
    match = _DURATION.fullmatch(value or "")
    if not match:
        return 0
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(max(seconds, 0), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _published(value: str) -> datetime:
    text = (value or "").replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return _as_utc(parsed)


def is_clickbait(title: str) -> bool:
    if _CLICKBAIT.search(title or ""):
        return True
    if (title or "").count("!") >= 3:
        return True
    letters = [char for char in title or "" if char.isalpha()]
    return len(letters) > 12 and all(char.isupper() for char in letters)


def _skill_tokens(skill: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9+#]+", " ", skill.lower())
    stop = {"for", "the", "and", "target", "with"}
    return [token for token in cleaned.split() if token and token not in stop]


def title_match(title: str, skill: str) -> float:
    """1 when every skill token is in the title, otherwise the share that match."""
    tokens = _skill_tokens(skill)
    if not tokens:
        return 0.0
    haystack = title.lower()
    hits = sum(1 for token in tokens if token in haystack)
    return hits / len(tokens)


def passes_filters(
    video: VideoCandidate,
    stage: str,
    skill_key: str,
    now: datetime,
) -> bool:
    """Drop videos that are not embeddable, the wrong length, too obscure, stale, or clickbait."""
    if not video.embeddable or not video.video_id:
        return False
    if is_clickbait(video.title):
        return False

    low, high, _target = STAGE_WINDOWS[stage]
    if video.duration_seconds < low or video.duration_seconds > high:
        return False

    minimum_views = MIN_VIEWS_JAPANESE if skill_key == "japanese" else MIN_VIEWS
    if video.views < minimum_views:
        return False

    years = FUNDAMENTAL_YEARS if skill_key in FUNDAMENTALS else FAST_MOVING_YEARS
    age_days = (_as_utc(now) - _as_utc(video.published_at)).days
    if age_days > years * 365:
        return False
    return True


def score_video(
    video: VideoCandidate,
    stage: str,
    skill: str,
    skill_key: str,
    now: datetime,
) -> float:
    """
    Transparent 0–1 score.

    Weights: views 0.30, like ratio 0.20, recency 0.15, duration fit 0.20, title match 0.15.
    """
    view_score = min(math.log10(video.views + 1) / 7, 1)
    like_ratio = video.likes / video.views if video.views else 0
    like_score = min(like_ratio / 0.05, 1)

    years = FUNDAMENTAL_YEARS if skill_key in FUNDAMENTALS else FAST_MOVING_YEARS
    age_days = max((_as_utc(now) - _as_utc(video.published_at)).days, 0)
    recency = max(0.0, 1 - age_days / (years * 365))

    _low, _high, target = STAGE_WINDOWS[stage]
    span = max((_high - _low) / 2, 1)
    duration_score = max(0.0, 1 - abs(video.duration_seconds - target) / span)

    return (
        0.30 * view_score
        + 0.20 * like_score
        + 0.15 * recency
        + 0.20 * duration_score
        + 0.15 * title_match(video.title, skill)
    )


def choose_videos(
    candidates_by_stage: dict[str, list[VideoCandidate]],
    skill: str,
    skill_key: str,
    now: datetime,
    excluded_ids: Optional[set[str]] = None,
) -> dict[str, Optional[VideoCandidate]]:
    """Pick the highest-scoring video for each stage. A video is used at most once."""
    used: set[str] = set(excluded_ids or ())
    chosen: dict[str, Optional[VideoCandidate]] = {}

    for stage in STAGES:
        viable: list[tuple[float, VideoCandidate]] = []
        for video in candidates_by_stage.get(stage, []):
            if video.video_id in used:
                continue
            if not passes_filters(video, stage, skill_key, now):
                continue
            viable.append((score_video(video, stage, skill, skill_key, now), video))
        if not viable:
            chosen[stage] = None
            continue
        viable.sort(key=lambda item: item[0], reverse=True)
        best = viable[0][1]
        used.add(best.video_id)
        chosen[stage] = best
    return chosen


def candidate_from_api_item(item: dict) -> Optional[VideoCandidate]:
    """Build a candidate from one videos.list item. Returns None when the id is missing."""
    video_id = item.get("id") or ""
    if isinstance(video_id, dict):
        video_id = video_id.get("videoId") or ""
    if not video_id:
        return None

    snippet = item.get("snippet") or {}
    thumbs = (snippet.get("thumbnails") or {})
    thumb = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {}).get("url") or ""
    stats = item.get("statistics") or {}
    status = item.get("status") or {}
    try:
        views = int(stats.get("viewCount") or 0)
    except (TypeError, ValueError):
        views = 0
    try:
        likes = int(stats.get("likeCount") or 0)
    except (TypeError, ValueError):
        likes = 0

    return VideoCandidate(
        video_id=video_id,
        title=snippet.get("title") or "",
        channel=snippet.get("channelTitle") or "",
        duration_seconds=parse_iso8601_duration((item.get("contentDetails") or {}).get("duration") or ""),
        views=views,
        likes=likes,
        published_at=_published(snippet.get("publishedAt") or ""),
        embeddable=bool(status.get("embeddable")),
        thumbnail=thumb,
    )


def candidates_from_videos_list(payload: dict) -> list[VideoCandidate]:
    """Parse a mocked or live videos.list response."""
    found: list[VideoCandidate] = []
    for item in payload.get("items") or []:
        candidate = candidate_from_api_item(item)
        if candidate:
            found.append(candidate)
    return found
