"""
AI analysis and ranked jobs routes.
"""

import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from database import delete_row, fetch_all, fetch_one, insert_row, update_row
from models.analysis import AnalysisResponse
from models.job import JobWithAnalysis
from models.user import UserResponse
from services.google_ai_service import google_ai_service
from utils.auth import get_current_user
from utils.ranking import aggregate_missing_skills, rank_jobs

router = APIRouter(tags=["Analysis"])

# One click scores a few listings, then stops, so Gemini is not flooded.
ANALYZE_BATCH = 3


def _merge_job_with_analysis(job: dict, analysis: Optional[dict]) -> JobWithAnalysis:
    """Combine job row and analysis row into a single response model."""
    merged = JobWithAnalysis(**job)
    if analysis:
        merged.compatibility_score = analysis.get("compatibility_score")
        merged.missing_skills = analysis.get("missing_skills")
        merged.matching_skills = analysis.get("matching_skills")
        merged.improvement_suggestions = analysis.get("improvement_suggestions")
        merged.ai_reasoning = analysis.get("ai_reasoning")
        merged.analysis_id = analysis.get("id")
    return merged


async def _run_analysis_for_job(user_id: str, job_id: str) -> AnalysisResponse:
    """Core analysis logic — fetch resume + job, call Gemini, save result."""
    job = fetch_one("jobs", {"id": job_id, "user_id": user_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resumes = fetch_all(
        "resumes",
        filters={"user_id": user_id},
        order_by="uploaded_at",
        ascending=False,
    )
    if not resumes:
        raise HTTPException(status_code=400, detail="Upload a resume before analyzing jobs.")

    resume_text = resumes[0].get("extracted_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume has no extracted text.")

    requirements = job.get("requirements")
    if isinstance(requirements, list):
        requirements = "\n".join(str(item) for item in requirements if item)

    try:
        result = await google_ai_service.analyze_job(
            resume_text=resume_text,
            job_title=job["job_title"],
            company=job["company"],
            description=job.get("description", "") or "",
            requirements=requirements or "",
        )
    except Exception as exc:
        err = str(exc)
        if "429" in err or "quota" in err.lower():
            raise HTTPException(
                status_code=502,
                detail="Google AI quota exceeded. Wait a minute and retry, or check billing at aistudio.google.com",
            ) from exc
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}") from exc

    # Upsert analysis — delete old if exists, insert new
    existing = fetch_one("analysis", {"job_id": job_id, "user_id": user_id})
    analysis_data = {
        "user_id": user_id,
        "job_id": job_id,
        "compatibility_score": result.compatibility_score,
        "missing_skills": result.missing_skills,
        "matching_skills": result.matching_skills,
        "improvement_suggestions": result.improvement_suggestions,
        "ai_reasoning": result.explanation,
    }

    if existing:
        row = update_row("analysis", str(existing["id"]), analysis_data)
    else:
        row = insert_row("analysis", analysis_data)

    return AnalysisResponse(**row)


@router.post("/analyze-job/{job_id}", response_model=AnalysisResponse)
async def analyze_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Analyze a single job against the user's resume using Google Gemini."""
    return await _run_analysis_for_job(str(current_user.id), str(job_id))


def _analyses_by_job(user_id: str) -> dict[str, dict]:
    rows = fetch_all("analysis", filters={"user_id": user_id})
    return {str(row.get("job_id")): row for row in rows}


@router.post("/analyze-all")
async def analyze_all_jobs(current_user: UserResponse = Depends(get_current_user)):
    """Score the next few jobs that do not already have a score."""
    user_id = str(current_user.id)
    jobs = fetch_all("jobs", filters={"user_id": user_id})
    scored = {
        job_id
        for job_id, row in _analyses_by_job(user_id).items()
        if row.get("compatibility_score") is not None
    }
    pending = [job for job in jobs if str(job["id"]) not in scored]
    results = []
    errors = []

    for index, job in enumerate(pending[:ANALYZE_BATCH]):
        if index:
            await asyncio.sleep(1.5)
        try:
            analysis = await _run_analysis_for_job(user_id, job["id"])
            results.append(
                {"job_id": str(job["id"]), "compatibility_score": analysis.compatibility_score}
            )
        except HTTPException as exc:
            errors.append({"job_id": job["id"], "error": exc.detail})
            if exc.status_code == 400 or "quota" in str(exc.detail).lower():
                break
        except Exception as exc:
            errors.append({"job_id": job["id"], "error": str(exc)})

    return {
        "total": len(jobs),
        "analyzed": len(results),
        "already_scored": len(scored),
        "remaining": len(pending) - len(results),
        "errors": errors,
        "results": results,
    }


@router.post("/reanalyze-job/{job_id}", response_model=AnalysisResponse)
async def reanalyze_job(
    job_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
):
    """Re-run AI analysis for a job (overwrites previous result)."""
    existing = fetch_one(
        "analysis",
        {"job_id": str(job_id), "user_id": str(current_user.id)},
    )
    if existing:
        delete_row("analysis", str(existing["id"]))
    return await _run_analysis_for_job(str(current_user.id), str(job_id))


def _fetch_ranked_jobs_for_user(
    user_id: str,
    min_score: Optional[int] = None,
    favorites_only: bool = False,
    search_query: Optional[str] = None,
) -> list[JobWithAnalysis]:
    """Internal helper — fetch and rank jobs without FastAPI Query defaults."""
    jobs = fetch_all(
        "jobs",
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=False,
    )
    analyses = _analyses_by_job(user_id)

    merged: list[JobWithAnalysis] = []
    for job in jobs:
        merged.append(_merge_job_with_analysis(job, analyses.get(str(job["id"]))))

    return rank_jobs(merged, min_score, favorites_only, search_query)


@router.get("/ranked-jobs", response_model=list[JobWithAnalysis])
async def get_ranked_jobs(
    min_score: Optional[int] = Query(None, ge=0, le=100),
    favorites_only: bool = Query(False),
    search_query: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get jobs ranked by compatibility score with optional filters."""
    return _fetch_ranked_jobs_for_user(
        str(current_user.id), min_score, favorites_only, search_query
    )


@router.get("/skills-gap")
async def get_skills_gap(current_user: UserResponse = Depends(get_current_user)):
    """Aggregate missing skills across all analyzed jobs."""
    ranked = _fetch_ranked_jobs_for_user(str(current_user.id))
    return aggregate_missing_skills(ranked)


@router.get("/export-report")
async def export_report(current_user: UserResponse = Depends(get_current_user)):
    """Export a JSON report of all ranked jobs and analysis."""
    ranked = _fetch_ranked_jobs_for_user(str(current_user.id))
    skills_gap = aggregate_missing_skills(ranked)

    report = {
        "user_id": str(current_user.id),
        "total_jobs": len(ranked),
        "analyzed_jobs": sum(1 for j in ranked if j.compatibility_score is not None),
        "average_score": (
            sum(j.compatibility_score for j in ranked if j.compatibility_score) /
            max(1, sum(1 for j in ranked if j.compatibility_score))
        ),
        "skills_gap": skills_gap,
        "jobs": [j.model_dump() for j in ranked],
    }
    return JSONResponse(content=report)
