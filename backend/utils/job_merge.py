"""
Merge and deduplicate jobs from multiple scraper sources.
"""

import json
import logging
from typing import Union

from models.job import JobBase
from models.scraped_job import ScrapedJob

logger = logging.getLogger(__name__)


def linkedin_job_to_scraped(job: JobBase) -> ScrapedJob:
    """Convert LinkedIn JobBase into standardized ScrapedJob format."""
    requirements: list[str] = []
    if job.requirements:
        try:
            parsed = json.loads(job.requirements)
            if isinstance(parsed, list):
                requirements = [str(r) for r in parsed]
            else:
                requirements = [job.requirements]
        except json.JSONDecodeError:
            requirements = [r.strip() for r in job.requirements.split(",") if r.strip()]

    return ScrapedJob(
        job_title=job.job_title,
        company=job.company,
        location=job.location or "",
        description=job.description or "",
        salary=job.salary or "",
        requirements=requirements,
        source_platform="linkedin",
        job_url=job.job_url or "",
    )


def normalize_to_scraped(jobs: list[Union[JobBase, ScrapedJob]]) -> list[ScrapedJob]:
    """Normalize a mixed list of JobBase / ScrapedJob into ScrapedJob instances."""
    normalized: list[ScrapedJob] = []
    for job in jobs:
        if isinstance(job, ScrapedJob):
            normalized.append(job)
        elif isinstance(job, JobBase):
            normalized.append(linkedin_job_to_scraped(job))
    return normalized


def _dedup_key(job: ScrapedJob) -> tuple[str, str, str]:
    return (
        job.job_title.lower().strip(),
        job.company.lower().strip(),
        (job.location or "").lower().strip(),
    )


def merge_and_deduplicate(jobs: list[Union[JobBase, ScrapedJob]]) -> list[ScrapedJob]:
    """
    Merge jobs from all sources and deduplicate by title + company + location.
    """
    merged = normalize_to_scraped(jobs)
    seen: set[tuple[str, str, str]] = set()
    unique: list[ScrapedJob] = []

    for job in merged:
        key = _dedup_key(job)
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    logger.info("Merged %d jobs into %d after deduplication", len(merged), len(unique))
    return unique
