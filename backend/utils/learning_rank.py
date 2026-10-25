"""
Rank missing skills for the Improve Your Skills section.

Priority is deterministic: how many analyzed jobs list the skill, weighted by
each job's compatibility score. No model calls.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

# Alias key -> canonical skill key. Keys are lowercase, with dots removed.
_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "postgre sql": "postgresql",
    "react": "react",
    "reactjs": "react",
    "react js": "react",
    "node": "nodejs",
    "nodejs": "nodejs",
    "node js": "nodejs",
    "py": "python",
    "python": "python",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "amazon web services": "aws",
    "aws": "aws",
    "golang": "go",
    "go": "go",
    "html": "html",
    "css": "css",
    "sql": "sql",
}

_DISPLAY = {
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "postgresql": "PostgreSQL",
    "react": "React",
    "nodejs": "Node.js",
    "python": "Python",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "go": "Go",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "c++": "C++",
    "c#": "C#",
}

# Rank 0 means no Japanese requirement, or the user has no usable level yet.
_USER_LEVEL_RANK = {
    None: 0,
    "": 0,
    "none": 0,
    "not sure": 0,
    "n5": 1,
    "n4": 2,
    "n3": 3,
    "n2": 4,
    "n1": 5,
    "native/fluent": 6,
}

_TARGET_LABEL = {
    1: "N5",
    2: "N4",
    3: "N3",
    4: "N2",
    5: "N1",
    6: "Native",
}

# First match wins. More specific phrases are listed before broader ones.
_JOB_LEVEL_PATTERNS = (
    (re.compile(r"not required|no japanese|\bnone\b"), 0),
    (re.compile(r"\bn5\b|basic"), 1),
    (re.compile(r"\bn4\b"), 2),
    (re.compile(r"\bn3\b|conversational"), 3),
    (re.compile(r"\bn2\b|business"), 4),
    (re.compile(r"\bn1\b|fluent"), 5),
    (re.compile(r"native"), 6),
)


@dataclass
class RankedJobInput:
    """One analyzed or unanalyzed job passed into the ranker."""

    job_id: str
    missing_skills: list[str] = field(default_factory=list)
    compatibility_score: Optional[int] = None
    japanese_level: Optional[str] = None


@dataclass
class RankedSkill:
    skill: str
    rank: int
    jobs_missing_count: int
    total_jobs: int
    demand_percent: int
    tier: str
    weight: float = 0.0


def canonical_skill(name: str) -> str:
    """Normalize a skill name for grouping. Empty string means ignore it."""
    text = name.strip().lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = text.replace(".", "")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return _ALIASES.get(text, text)


def is_japanese_skill_name(name: str) -> bool:
    """True when a free-text skill is really a Japanese-language mention."""
    key = canonical_skill(name)
    return key in {"japanese", "jlpt"} or key.startswith("jlpt ") or key.startswith("japanese ")


def job_japanese_rank(level: Optional[str]) -> int:
    """Map a scraped job Japanese string onto the shared rank scale."""
    if not level or not level.strip():
        return 0
    text = level.strip().lower()
    for pattern, rank in _JOB_LEVEL_PATTERNS:
        if pattern.search(text):
            return rank
    return 0


def user_japanese_rank(level: Optional[str]) -> int:
    """Map a saved profile level onto the shared rank scale."""
    if level is None:
        return 0
    return _USER_LEVEL_RANK.get(level.strip().lower(), 0)


def demand_tier(percent: int) -> str:
    if percent >= 60:
        return "High"
    if percent >= 30:
        return "Medium"
    return "Low"


def _percent(count: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(100 * count / total + 0.5)


def _display_name(canonical: str, first_seen: str) -> str:
    if canonical in _DISPLAY:
        return _DISPLAY[canonical]
    cleaned = re.sub(r"\s+", " ", first_seen).strip()
    return cleaned or canonical


def _japanese_target(jobs: list[RankedJobInput], user_level: Optional[str]) -> Optional[tuple[str, int, float]]:
    """
    Return (label, job count, weight) when matched jobs need more Japanese
    than the user has. The label is the most common required level; ties
    go to the higher level.
    """
    user_rank = user_japanese_rank(user_level)
    counts: Counter[int] = Counter()
    weight = 0.0
    job_count = 0

    for job in jobs:
        if job.compatibility_score is None:
            continue
        required = job_japanese_rank(job.japanese_level)
        if required <= user_rank:
            continue
        counts[required] += 1
        job_count += 1
        weight += job.compatibility_score / 100

    if not counts:
        return None

    required_rank = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)[0][0]
    label = _TARGET_LABEL.get(required_rank, "N3")
    return f"Japanese (target {label})", job_count, weight


def rank_learning_skills(
    jobs: list[RankedJobInput],
    user_japanese_level: Optional[str] = None,
    top_n: int = 5,
) -> list[RankedSkill]:
    """
    Rank skills for a learning plan.

    Only jobs with a compatibility score count as matched jobs. Japanese is
    added from the scraped job level, not from free-text missing skills.
    """
    matched = [job for job in jobs if job.compatibility_score is not None]
    total = len(matched)
    if total == 0:
        return []

    counts: dict[str, set[str]] = {}
    weights: dict[str, float] = {}
    labels: dict[str, str] = {}

    for job in matched:
        score_weight = (job.compatibility_score or 0) / 100
        seen: set[str] = set()
        for raw in job.missing_skills or []:
            if is_japanese_skill_name(raw):
                continue
            key = canonical_skill(raw)
            if not key or key in seen:
                continue
            seen.add(key)
            counts.setdefault(key, set()).add(job.job_id)
            weights[key] = weights.get(key, 0.0) + score_weight
            labels.setdefault(key, _display_name(key, raw))

    ranked: list[tuple[str, int, float]] = [
        (labels[key], len(job_ids), weights.get(key, 0.0))
        for key, job_ids in counts.items()
    ]

    japanese = _japanese_target(matched, user_japanese_level)
    japanese_label = japanese[0] if japanese else None
    if japanese:
        ranked.append(japanese)

    ranked.sort(key=lambda item: (-item[2], -item[1], item[0].lower()))

    selected = ranked[:top_n]
    if japanese_label and all(item[0] != japanese_label for item in selected):
        selected.append(japanese)

    results: list[RankedSkill] = []
    for index, (skill, count, weight) in enumerate(selected, start=1):
        percent = _percent(count, total)
        results.append(
            RankedSkill(
                skill=skill,
                rank=index,
                jobs_missing_count=count,
                total_jobs=total,
                demand_percent=percent,
                tier=demand_tier(percent),
                weight=weight,
            )
        )
    return results
