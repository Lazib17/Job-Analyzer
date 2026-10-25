"""Scoring tests use mocked YouTube API payloads. No network calls."""

from datetime import datetime, timezone

from services.reading_resources import readings_for_skill
from services.youtube_resources import videos_for_skill
from utils.youtube_rank import (
    VideoCandidate,
    candidates_from_videos_list,
    choose_videos,
    passes_filters,
    score_video,
)

NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)


def _video(**overrides) -> VideoCandidate:
    data = {
        "video_id": "good",
        "title": "Python for beginners crash course",
        "channel": "Example",
        "duration_seconds": 20 * 60,
        "views": 1_000_000,
        "likes": 50_000,
        "published_at": datetime(2024, 6, 1, tzinfo=timezone.utc),
        "embeddable": True,
        "thumbnail": "https://i.ytimg.com/vi/good/mqdefault.jpg",
    }
    data.update(overrides)
    return VideoCandidate(**data)


def _api_item(video_id, title, duration, views, likes, published, embeddable=True):
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "channelTitle": "Example",
            "publishedAt": published,
            "thumbnails": {"medium": {"url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"}},
        },
        "contentDetails": {"duration": duration},
        "statistics": {"viewCount": str(views), "likeCount": str(likes)},
        "status": {"embeddable": embeddable},
    }


def test_score_prefers_relevant_popular_video():
    strong = _video()
    weak = _video(
        video_id="weak",
        title="unrelated office hours",
        views=2_000,
        likes=10,
        duration_seconds=55 * 60,
    )
    assert score_video(strong, "intro", "Python", "python", NOW) > score_video(
        weak, "intro", "Python", "python", NOW
    )


def test_filters_drop_bad_videos_and_keep_older_fundamentals():
    assert not passes_filters(_video(embeddable=False), "intro", "python", NOW)
    assert not passes_filters(_video(duration_seconds=60), "intro", "python", NOW)
    assert not passes_filters(_video(views=12), "intro", "python", NOW)
    assert not passes_filters(
        _video(title="SHOCKING PYTHON HACK YOU WON'T BELIEVE!!!"),
        "intro",
        "python",
        NOW,
    )
    old = datetime(2018, 1, 1, tzinfo=timezone.utc)
    assert not passes_filters(_video(published_at=old), "intro", "react", NOW)
    assert passes_filters(
        _video(title="Git for beginners crash course", published_at=old),
        "intro",
        "git",
        NOW,
    )


def test_mocked_api_payload_picks_one_video_per_stage_without_repeats():
    payload = {
        "items": [
            _api_item("good", "Python for beginners crash course", "PT20M", 900_000, 40_000, "2024-06-01T00:00:00Z"),
            _api_item("click", "SHOCKING PYTHON HACK YOU WON'T BELIEVE!!!", "PT15M", 2_000_000, 10_000, "2025-01-01T00:00:00Z"),
            _api_item("tiny", "Python for beginners crash course", "PT3M", 500_000, 20_000, "2024-01-01T00:00:00Z"),
            _api_item("deep", "Python in depth tutorial explained", "PT1H", 400_000, 20_000, "2023-05-01T00:00:00Z"),
            _api_item("same", "Python for beginners crash course", "PT20M", 100_000, 5_000, "2024-02-01T00:00:00Z"),
        ]
    }
    candidates = candidates_from_videos_list(payload)
    by_id = {item.video_id: item for item in candidates}
    chosen = choose_videos(
        {
            "intro": [by_id["good"], by_id["click"], by_id["tiny"], by_id["same"]],
            "deep_dive": [by_id["good"], by_id["deep"]],
            "project": [by_id["good"]],
        },
        skill="Python",
        skill_key="python",
        now=NOW,
    )
    assert chosen["intro"].video_id == "good"
    assert chosen["deep_dive"].video_id == "deep"
    assert chosen["project"] is None
    assert len({item.video_id for item in chosen.values() if item}) == 2


def test_missing_api_key_returns_search_links():
    videos = videos_for_skill("Python", api_key="")
    assert len(videos) == 3
    assert [item["stage"] for item in videos] == ["intro", "deep_dive", "project"]
    assert all(item["kind"] == "search_link" for item in videos)
    assert all(item["videoId"] is None for item in videos)
    assert all(item["url"].startswith("https://www.youtube.com/results?search_query=") for item in videos)


def test_curated_readings_and_search_fallback():
    javascript = readings_for_skill("JavaScript")
    assert javascript[0]["kind"] == "resource"
    assert "developer.mozilla.org" in javascript[0]["url"]

    japanese = readings_for_skill("Japanese (target N3)")
    assert any("jlpt.jp" in item["url"] for item in japanese)
    assert all(item["kind"] == "resource" for item in japanese)

    unknown = readings_for_skill("Underwater Basket Weaving")
    assert unknown[0]["kind"] == "search_link"
    assert unknown[0]["url"].startswith("https://www.google.com/search?q=")
