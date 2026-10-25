"""Create and store a week-by-week learning plan."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from config import settings
from database import fetch_all, fetch_one, insert_row, update_row
from services.google_ai_service import google_ai_service
from services.reading_resources import readings_for_skill, subject_for_skill
from services.youtube_resources import search_link, stage_query, videos_for_skill
from utils.learning_plan import PlanDraft, generate_plan_with_retry, index_resources

logger = logging.getLogger(__name__)

PLAN_SYSTEM = """You are a careful study-plan writer.
Return valid JSON only. Do not write URLs. Refer to learning materials only by the resource ids you are given."""


def _resources_for(skill: str) -> list[dict]:
    try:
        videos = videos_for_skill(skill)
    except Exception:
        logger.warning("Video lookup failed while building a plan", exc_info=True)
        queries = stage_query(skill)
        videos = [search_link(stage, query) for stage, query in queries.items()]
    return index_resources(videos, readings_for_skill(skill))


def _prompt(
    skill: str,
    duration_weeks: int,
    hours_per_week: int,
    japanese_level: Optional[str],
    resources: list[dict],
    error: Optional[str],
) -> str:
    lines = [
        f"Skill: {skill}",
        f"Weeks: {duration_weeks}",
        f"Hours per week: {hours_per_week}",
        f"Minute budget per week: {hours_per_week * 60}",
    ]
    _key, level = subject_for_skill(skill)
    if level or japanese_level:
        lines.append(f"Learner Japanese level: {japanese_level or 'not set'}")
        if level:
            lines.append(f"Target Japanese level: {level}")
    lines.append("Resources (use only these ids, never invent urls):")
    for item in resources:
        lines.append(f"- {item['id']}: {item['title']} ({item['kind']})")
    lines.append(
        "Flow: intro video and a reading in week 1, deep dive and practice in the middle, "
        "project video and a self-directed project near the end, review in the last week."
    )
    lines.append(
        'Return JSON: {"weeks":[{"goal":"...","tasks":[{"type":"watch|read|practice|project|review",'
        '"title":"...","resource_id":"id or null","estimated_minutes":30}]}]}'
    )
    lines.append(f"The weeks array must contain exactly {duration_weeks} weeks.")
    lines.append("Each week's estimated_minutes must add up to no more than the minute budget.")
    if error:
        lines.append(f"The previous plan was rejected: {error}")
        lines.append("Return a corrected JSON plan.")
    return "\n".join(lines)


def draft_plan(
    skill: str,
    duration_weeks: int,
    hours_per_week: int,
    japanese_level: Optional[str],
) -> tuple[PlanDraft, str, list[dict]]:
    resources = _resources_for(skill)
    if not settings.google_api_key:
        from utils.learning_plan import build_template_plan

        logger.info("GOOGLE_API_KEY is not set — using the template study plan")
        return build_template_plan(skill, duration_weeks, hours_per_week, resources), "template", resources

    def generate(error: Optional[str]) -> dict:
        return google_ai_service.generate_json(
            _prompt(skill, duration_weeks, hours_per_week, japanese_level, resources, error),
            system_instruction=PLAN_SYSTEM,
            max_output_tokens=8192,
            temperature=0.4,
        )

    plan, source = generate_plan_with_retry(
        generate,
        skill=skill,
        duration_weeks=duration_weeks,
        hours_per_week=hours_per_week,
        resources=resources,
    )
    return plan, source, resources


def save_plan(
    user_id: str,
    skill: str,
    duration_weeks: int,
    hours_per_week: int,
    start_date: Optional[date],
    study_days: Optional[list[str]],
    japanese_level: Optional[str],
    source: str,
    plan: PlanDraft,
    resources: list[dict],
) -> dict:
    by_id = {item["id"]: item for item in resources}
    created = insert_row(
        "learning_plans",
        {
            "user_id": user_id,
            "skill": skill,
            "duration_weeks": duration_weeks,
            "hours_per_week": hours_per_week,
            "start_date": start_date.isoformat() if start_date else None,
            "study_days": study_days,
            "japanese_level": japanese_level,
            "source": source,
        },
    )
    plan_id = str(created["id"])
    for number, week in enumerate(plan.weeks, start=1):
        week_row = insert_row(
            "learning_plan_weeks",
            {"plan_id": plan_id, "week_number": number, "goal": week.goal},
        )
        for position, task in enumerate(week.tasks):
            snapshot = None
            if task.resource_id and task.resource_id in by_id:
                item = by_id[task.resource_id]
                snapshot = _resource_snapshot(item)
            insert_row(
                "learning_plan_tasks",
                {
                    "plan_id": plan_id,
                    "week_id": str(week_row["id"]),
                    "position": position,
                    "task_type": task.type,
                    "title": task.title,
                    "resource_id": task.resource_id,
                    "resource_snapshot": snapshot,
                    "estimated_minutes": task.estimated_minutes,
                    "done": False,
                },
            )
    return load_plan(plan_id, user_id)


def _resource_snapshot(item: dict) -> dict:
    snapshot = {
        "title": item.get("title") or "",
        "url": item.get("url") or "",
        "kind": item.get("kind") or "resource",
    }
    for source_key, target_key in (
        ("video_id", "videoId"),
        ("channel", "channel"),
        ("duration", "duration"),
        ("views", "views"),
        ("thumbnail", "thumbnail"),
        ("source", "source"),
    ):
        value = item.get(source_key)
        if value not in (None, ""):
            snapshot[target_key] = value
    return snapshot


def _as_text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime) or isinstance(value, date):
        return value.isoformat()
    return str(value)


def _snapshot(value) -> Optional[dict]:
    if isinstance(value, dict):
        return value
    return None


def load_plan(plan_id: str, user_id: str) -> dict:
    plan = fetch_one("learning_plans", {"id": plan_id, "user_id": user_id})
    if not plan:
        return {}
    weeks = fetch_all("learning_plan_weeks", filters={"plan_id": plan_id}, order_by="week_number", ascending=True)
    tasks = fetch_all("learning_plan_tasks", filters={"plan_id": plan_id})
    tasks_by_week: dict[str, list[dict]] = {}
    for task in tasks:
        tasks_by_week.setdefault(str(task["week_id"]), []).append(task)

    week_payload = []
    done = 0
    total = 0
    for week in weeks:
        week_tasks = sorted(tasks_by_week.get(str(week["id"]), []), key=lambda item: item.get("position") or 0)
        rendered = []
        for task in week_tasks:
            total += 1
            if task.get("done"):
                done += 1
            rendered.append(
                {
                    "id": str(task["id"]),
                    "type": task["task_type"],
                    "title": task["title"],
                    "resource_id": task.get("resource_id"),
                    "resource": _snapshot(task.get("resource_snapshot")),
                    "estimated_minutes": task["estimated_minutes"],
                    "done": bool(task.get("done")),
                }
            )
        week_payload.append(
            {
                "week_number": week["week_number"],
                "goal": week["goal"],
                "tasks": rendered,
            }
        )
    return {
        "id": str(plan["id"]),
        "skill": plan["skill"],
        "duration_weeks": plan["duration_weeks"],
        "hours_per_week": plan["hours_per_week"],
        "start_date": _as_text(plan.get("start_date")),
        "study_days": plan.get("study_days"),
        "japanese_level": plan.get("japanese_level"),
        "source": plan["source"],
        "created_at": _as_text(plan.get("created_at")),
        "progress": {"done": done, "total": total},
        "weeks": week_payload,
    }


def list_plans(user_id: str) -> list[dict]:
    plans = fetch_all("learning_plans", filters={"user_id": user_id}, order_by="created_at", ascending=False)
    summaries = []
    for plan in plans:
        full = load_plan(str(plan["id"]), user_id)
        if not full:
            continue
        summaries.append(
            {
                "id": full["id"],
                "skill": full["skill"],
                "duration_weeks": full["duration_weeks"],
                "hours_per_week": full["hours_per_week"],
                "start_date": full["start_date"],
                "source": full["source"],
                "created_at": full["created_at"],
                "progress": full["progress"],
            }
        )
    return summaries


def set_task_done(plan_id: str, task_id: str, user_id: str, done: bool) -> Optional[dict]:
    plan = fetch_one("learning_plans", {"id": plan_id, "user_id": user_id})
    if not plan:
        return None
    task = fetch_one("learning_plan_tasks", {"id": task_id, "plan_id": plan_id})
    if not task:
        return None
    update_row("learning_plan_tasks", task_id, {"done": done})
    return load_plan(plan_id, user_id)
