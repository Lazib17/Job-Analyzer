"""
Job search, listing, and favorites routes.
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from database import fetch_all, fetch_one, insert_row, update_row
from models.job import JobResponse, JobSearchRequest, JobWithAnalysis
from models.scraped_job import ScrapedJob
from models.user import UserResponse
from utils.auth import get_current_user
from utils.job_merge import merge_and_deduplicate
from utils.job_storage import scraped_job_to_db_row

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Jobs"])


async def _safe_scrape(scraper_name: str, coro) -> list:
    """Run a scraper coroutine without failing the entire pipeline."""
    try:
        return await coro
    except Exception as exc:
        logger.error("%s scraper failed: %s", scraper_name, exc)
        return []


def _insert_job_row(job: ScrapedJob, user_id: str) -> dict:
    """Insert job into Supabase, falling back if platform columns are missing."""
    row = scraped_job_to_db_row(job, user_id)
    try:
        return insert_row("jobs", row)
    except Exception:
        # Fallback for databases without platform migration applied yet
        core_row = {
            k: v
            for k, v in row.items()
            if k
            in {
                "user_id",
                "job_title",
                "company",
                "location",
                "description",
                "salary",
                "requirements",
                "job_url",
            }
        }
        return insert_row("jobs", core_row)


@router.post("/search-jobs", response_model=list[JobResponse])
async def search_jobs(
    search: JobSearchRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Scrape jobs from all platforms, merge, deduplicate, and save to database.
    """
    from services.career_cross_scraper import career_cross_scraper
    from services.gaijinpot_scraper import gaijinpot_scraper
    from services.mynavi_scraper import mynavi_scraper
    from services.wantedly_scraper import wantedly_scraper

    per_source_limit = max(5, search.max_results // 4)

    mynavi_jobs, career_cross_jobs, wantedly_jobs, gaijinpot_jobs = await asyncio.gather(
        _safe_scrape(
            "Mynavi",
            mynavi_scraper.search_jobs(
                job_title=search.job_title,
                location=search.location,
                max_results=per_source_limit,
            ),
        ),
        _safe_scrape(
            "CareerCross",
            career_cross_scraper.search_jobs(
                job_title=search.job_title,
                location=search.location,
                max_results=per_source_limit,
            ),
        ),
        _safe_scrape(
            "Wantedly",
            wantedly_scraper.search_jobs(
                job_title=search.job_title,
                location=search.location,
                max_results=per_source_limit,
            ),
        ),
        _safe_scrape(
            "GaijinPot",
            gaijinpot_scraper.search_jobs(
                job_title=search.job_title,
                location=search.location,
                max_results=per_source_limit,
            ),
        ),
    )

    if not mynavi_jobs and not career_cross_jobs and not wantedly_jobs and not gaijinpot_jobs:
        raise HTTPException(
            status_code=503,
            detail="All job sources failed. Please try again later.",
        )

    all_jobs = (
        list(mynavi_jobs)
        + list(career_cross_jobs)
        + list(wantedly_jobs)
        + list(gaijinpot_jobs)
    )
    merged_jobs = merge_and_deduplicate(all_jobs)

    saved_jobs: list[JobResponse] = []
    for job in merged_jobs:
        row = _insert_job_row(job, str(current_user.id))
        saved_jobs.append(JobResponse(**row))

    insert_row(
        "search_history",
        {
            "user_id": str(current_user.id),
            "job_title": search.job_title,
            "location": search.location,
            "results_count": len(saved_jobs),
        },
    )

    return saved_jobs


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(current_user: UserResponse = Depends(get_current_user)):
    """Get all jobs for the current user."""
    jobs = fetch_all(
        "jobs",
        filters={"user_id": str(current_user.id)},
        order_by="created_at",
        ascending=False,
    )
    return [JobResponse(**j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobWithAnalysis)
async def get_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a single job with its analysis data if available."""
    job = fetch_one("jobs", {"id": str(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    analysis = fetch_one("analysis", {"job_id": str(job_id), "user_id": str(current_user.id)})
    job_data = JobWithAnalysis(**job)
    if analysis:
        job_data.compatibility_score = analysis.get("compatibility_score")
        job_data.missing_skills = analysis.get("missing_skills")
        job_data.matching_skills = analysis.get("matching_skills")
        job_data.improvement_suggestions = analysis.get("improvement_suggestions")
        job_data.ai_reasoning = analysis.get("ai_reasoning")
        job_data.analysis_id = analysis.get("id")

    return job_data


@router.post("/jobs/{job_id}/favorite", response_model=JobResponse)
async def toggle_favorite(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Toggle favorite status for a job."""
    job = fetch_one("jobs", {"id": str(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    updated = update_row(
        "jobs",
        str(job_id),
        {"is_favorite": not job.get("is_favorite", False)},
    )
    return JobResponse(**updated)


@router.get("/search-history")
async def get_search_history(current_user: UserResponse = Depends(get_current_user)):
    """Get user's job search history."""
    history = fetch_all(
        "search_history",
        filters={"user_id": str(current_user.id)},
        order_by="searched_at",
        ascending=False,
    )
    return history
