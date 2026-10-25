"""Learning-plan inputs: ranked skills, resources, and saved plans."""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query

from database import fetch_one
from models.learning import (
    JAPANESE_LEVELS,
    LearningPlanResponse,
    LearningPlanSummaryResponse,
    LearningReadingResponse,
    LearningResourcesResponse,
    LearningSkillResponse,
    LearningSkillsResponse,
    LearningVideoResponse,
    PlanCreateRequest,
    TaskProgressRequest,
)
from services.learning_plans import draft_plan, list_plans, load_plan, save_plan, set_task_done
from models.user import UserResponse
from routes.analysis import _fetch_ranked_jobs_for_user
from services.reading_resources import readings_for_skill
from services.youtube_resources import search_link, stage_query, videos_for_skill
from utils.auth import get_current_user
from utils.learning_rank import RankedJobInput, rank_learning_skills

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Learning"])

_PLAN_HITS: dict[str, list[float]] = defaultdict(list)
_MAX_PLANS_PER_HOUR = 5


def _enforce_plan_rate_limit(user_id: str) -> None:
    now = time.time()
    recent = [stamp for stamp in _PLAN_HITS[user_id] if now - stamp < 3600]
    if len(recent) >= _MAX_PLANS_PER_HOUR:
        raise HTTPException(status_code=429, detail="You can generate up to 5 plans per hour.")
    recent.append(now)
    _PLAN_HITS[user_id] = recent


def _saved_japanese_level(user_id: str) -> str | None:
    user = fetch_one("users", {"id": user_id}) or {}
    level = user.get("japanese_level")
    if level not in JAPANESE_LEVELS:
        return None
    return level


@router.get("/learning/skills", response_model=LearningSkillsResponse)
async def get_learning_skills(current_user: UserResponse = Depends(get_current_user)):
    """Rank missing skills from the user's analyzed jobs."""
    user_id = str(current_user.id)
    jobs = _fetch_ranked_jobs_for_user(user_id)
    level = _saved_japanese_level(user_id)
    inputs = [
        RankedJobInput(
            job_id=str(job.id),
            missing_skills=list(job.missing_skills or []),
            compatibility_score=job.compatibility_score,
            japanese_level=job.japanese_level,
        )
        for job in jobs
    ]
    ranked = rank_learning_skills(inputs, user_japanese_level=level)
    total = ranked[0].total_jobs if ranked else sum(1 for job in inputs if job.compatibility_score is not None)
    return LearningSkillsResponse(
        total_jobs=total,
        japanese_level=level,
        skills=[
            LearningSkillResponse(
                skill=item.skill,
                rank=item.rank,
                jobs_missing_count=item.jobs_missing_count,
                total_jobs=item.total_jobs,
                demand_percent=item.demand_percent,
                tier=item.tier,
            )
            for item in ranked
        ],
    )


@router.get("/learning/resources", response_model=LearningResourcesResponse)
async def get_learning_resources(
    skill: str = Query(..., min_length=1, max_length=120),
    current_user: UserResponse = Depends(get_current_user),
):
    """Three videos and curated readings for one skill. Requires a signed-in user."""
    try:
        videos = videos_for_skill(skill)
    except Exception:
        queries = stage_query(skill)
        videos = [search_link(stage, query) for stage, query in queries.items()]
    readings = readings_for_skill(skill)
    return LearningResourcesResponse(
        skill=skill,
        videos=[LearningVideoResponse(**item) for item in videos],
        readings=[LearningReadingResponse(**item) for item in readings],
    )


@router.post("/learning/plans", response_model=LearningPlanResponse)
async def create_learning_plan(
    body: PlanCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Generate a week-by-week plan and save it for this user."""
    user_id = str(current_user.id)
    _enforce_plan_rate_limit(user_id)
    level = _saved_japanese_level(user_id)
    try:
        draft, source, resources = draft_plan(
            body.skill,
            body.duration_weeks,
            body.hours_per_week,
            level,
        )
        saved = save_plan(
            user_id=user_id,
            skill=body.skill,
            duration_weeks=body.duration_weeks,
            hours_per_week=body.hours_per_week,
            start_date=body.start_date,
            study_days=body.study_days,
            japanese_level=level,
            source=source,
            plan=draft,
            resources=resources,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not save learning plan")
        raise HTTPException(
            status_code=503,
            detail="Could not save the plan. Run supabase/migration_learning_plans.sql in the SQL Editor.",
        ) from None
    return saved


@router.get("/learning/plans", response_model=list[LearningPlanSummaryResponse])
async def get_learning_plans(current_user: UserResponse = Depends(get_current_user)):
    """List the signed-in user's saved plans."""
    try:
        return list_plans(str(current_user.id))
    except Exception:
        logger.exception("Could not list learning plans")
        raise HTTPException(
            status_code=503,
            detail="Could not load plans. Run supabase/migration_learning_plans.sql in the SQL Editor.",
        ) from None


@router.get("/learning/plans/{plan_id}", response_model=LearningPlanResponse)
async def get_learning_plan(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Return one plan, including weeks and task progress."""
    plan = load_plan(plan_id, str(current_user.id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.patch("/learning/plans/{plan_id}/tasks/{task_id}", response_model=LearningPlanResponse)
async def update_learning_task(
    plan_id: str,
    task_id: str,
    body: TaskProgressRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Mark one plan task done or not done."""
    plan = set_task_done(plan_id, task_id, str(current_user.id), body.done)
    if not plan:
        raise HTTPException(status_code=404, detail="Task not found")
    return plan
