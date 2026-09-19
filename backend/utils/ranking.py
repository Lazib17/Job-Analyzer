"""
Job ranking utilities — sort and filter jobs by compatibility score.
"""

from typing import Optional

from models.job import JobWithAnalysis


def rank_jobs(
    jobs: list[JobWithAnalysis],
    min_score: Optional[int] = None,
    favorites_only: bool = False,
    search_query: Optional[str] = None,
) -> list[JobWithAnalysis]:
    """
    Rank jobs by compatibility score (descending).
    Apply optional filters for score, favorites, and text search.
    """
    filtered = jobs

    if min_score is not None:
        filtered = [
            j for j in filtered
            if j.compatibility_score is not None and j.compatibility_score >= min_score
        ]

    if favorites_only:
        filtered = [j for j in filtered if j.is_favorite]

    if search_query:
        query = search_query.lower()
        filtered = [
            j for j in filtered
            if query in j.job_title.lower()
            or query in j.company.lower()
            or (j.location and query in j.location.lower())
        ]

    # Sort by score descending; jobs without scores go to the end
    return sorted(
        filtered,
        key=lambda j: (j.compatibility_score is not None, j.compatibility_score or 0),
        reverse=True,
    )


def score_tier(score: Optional[int]) -> str:
    """Return a human-readable tier label for a compatibility score."""
    if score is None:
        return "unrated"
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "low"


def aggregate_missing_skills(jobs: list[JobWithAnalysis], top_n: int = 10) -> list[dict]:
    """
    Aggregate missing skills across all analyzed jobs.
    Returns the most frequently missing skills.
    """
    skill_counts: dict[str, int] = {}
    for job in jobs:
        if job.missing_skills:
            for skill in job.missing_skills:
                normalized = skill.strip().lower()
                if normalized:
                    skill_counts[normalized] = skill_counts.get(normalized, 0) + 1

    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return [
        {"skill": skill.title(), "count": count}
        for skill, count in sorted_skills[:top_n]
    ]
