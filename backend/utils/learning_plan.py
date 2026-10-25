"""Validate a generated study plan and build a deterministic fallback."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

TASK_TYPES = ("watch", "read", "practice", "project", "review")


class PlanTaskDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    title: str = Field(min_length=1, max_length=200)
    resource_id: Optional[str] = None
    estimated_minutes: int = Field(ge=1, le=20 * 60)

    @field_validator("type")
    @classmethod
    def _type(cls, value: str) -> str:
        if value not in TASK_TYPES:
            raise ValueError(f"task type must be one of {', '.join(TASK_TYPES)}")
        return value

    @field_validator("resource_id", mode="before")
    @classmethod
    def _blank_resource(cls, value):
        if value is None or value == "":
            return None
        return str(value)


class PlanWeekDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    goal: str = Field(min_length=1, max_length=300)
    tasks: list[PlanTaskDraft] = Field(min_length=1)


class PlanDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    weeks: list[PlanWeekDraft]


def budget_minutes(hours_per_week: int) -> int:
    return hours_per_week * 60


def validate_plan(
    raw: dict,
    *,
    duration_weeks: int,
    hours_per_week: int,
    allowed_resource_ids: set[str],
) -> PlanDraft:
    """
    Reject a plan that has the wrong number of weeks, an unknown resource id,
    or a week whose tasks exceed hours_per_week × 60 minutes.
    """
    try:
        plan = PlanDraft.model_validate(raw)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid plan"
        raise ValueError(message) from exc

    if len(plan.weeks) != duration_weeks:
        raise ValueError(f"Expected {duration_weeks} weeks, got {len(plan.weeks)}")

    budget = budget_minutes(hours_per_week)
    for index, week in enumerate(plan.weeks, start=1):
        total = sum(task.estimated_minutes for task in week.tasks)
        if total > budget:
            raise ValueError(
                f"Week {index} totals {total} minutes, which is over the {budget} minute budget"
            )
        for task in week.tasks:
            if task.resource_id and task.resource_id not in allowed_resource_ids:
                raise ValueError(f"Unknown resource_id {task.resource_id}")
    return plan


def index_resources(videos: list[dict], readings: list[dict]) -> list[dict]:
    """Stable ids the model is allowed to cite. video:{stage} and reading:{n}."""
    indexed: list[dict] = []
    for video in videos:
        stage = video.get("stage") or "intro"
        indexed.append(
            {
                "id": f"video:{stage}",
                "kind": video.get("kind") or "search_link",
                "title": video.get("title") or stage,
                "url": video.get("url") or "",
                "minutes": _video_minutes(video),
                "video_id": video.get("videoId"),
                "channel": video.get("channel"),
                "duration": video.get("duration"),
                "views": video.get("views"),
                "thumbnail": video.get("thumbnail"),
            }
        )
    for number, reading in enumerate(readings, start=1):
        minutes = reading.get("estimated_minutes") or 25
        indexed.append(
            {
                "id": f"reading:{number}",
                "kind": reading.get("kind") or "resource",
                "title": reading.get("title") or f"Reading {number}",
                "url": reading.get("url") or "",
                "minutes": int(minutes),
                "source": reading.get("source"),
            }
        )
    return indexed


def _video_minutes(video: dict) -> int:
    defaults = {"intro": 30, "deep_dive": 45, "project": 45}
    duration = video.get("duration") or ""
    parts = [int(part) for part in str(duration).split(":") if part.isdigit()]
    if len(parts) == 3:
        minutes = parts[0] * 60 + parts[1]
    elif len(parts) == 2:
        minutes = parts[0]
    else:
        minutes = defaults.get(video.get("stage"), 30)
    return max(15, min(minutes, 90))


def _task(task_type: str, title: str, resource_id: Optional[str], minutes: int, budget: int) -> dict:
    return {
        "type": task_type,
        "title": title[:200],
        "resource_id": resource_id,
        "estimated_minutes": max(1, min(minutes, budget)),
    }


def build_template_plan(
    skill: str,
    duration_weeks: int,
    hours_per_week: int,
    resources: list[dict],
) -> PlanDraft:
    """A plan that always fits the time budget when the model output cannot."""
    budget = budget_minutes(hours_per_week)
    by_id = {item["id"]: item for item in resources}
    queue: list[dict] = []

    intro = by_id.get("video:intro")
    if intro:
        queue.append(_task("watch", f"Watch: {intro['title']}", "video:intro", intro["minutes"], budget))
    readings = [item for item in resources if item["id"].startswith("reading:")]
    if readings:
        queue.append(_task("read", f"Read: {readings[0]['title']}", readings[0]["id"], readings[0]["minutes"], budget))

    deep = by_id.get("video:deep_dive")
    if deep:
        queue.append(_task("watch", f"Watch: {deep['title']}", "video:deep_dive", deep["minutes"], budget))
    for reading in readings[1:]:
        queue.append(_task("read", f"Read: {reading['title']}", reading["id"], reading["minutes"], budget))

    project = by_id.get("video:project")
    if project:
        queue.append(_task("watch", f"Watch: {project['title']}", "video:project", project["minutes"], budget))
    queue.append(_task("project", f"Build a small {skill} project", project["id"] if project else None, 45, budget))
    queue.append(_task("review", f"Review what you learned about {skill}", None, 20, budget))

    while len(queue) < duration_weeks:
        queue.insert(-1, _task("practice", f"Practice {skill}", None, 30, budget))

    weeks: list[dict] = [
        {"goal": _goal(index, duration_weeks, skill), "tasks": []}
        for index in range(1, duration_weeks + 1)
    ]
    used = [0] * duration_weeks
    cursor = 0
    for task in queue:
        placed = False
        for _ in range(duration_weeks):
            if used[cursor] + task["estimated_minutes"] <= budget:
                weeks[cursor]["tasks"].append(dict(task))
                used[cursor] += task["estimated_minutes"]
                placed = True
                cursor = (cursor + 1) % duration_weeks
                break
            cursor = (cursor + 1) % duration_weeks
        if placed:
            continue
        emptiest = min(range(duration_weeks), key=lambda index: used[index])
        room = budget - used[emptiest]
        if room < 1:
            continue
        shrunk = dict(task)
        shrunk["estimated_minutes"] = room
        weeks[emptiest]["tasks"].append(shrunk)
        used[emptiest] += room

    for index, week in enumerate(weeks):
        if week["tasks"]:
            continue
        minutes = min(20, budget)
        week["tasks"].append(_task("practice", f"Practice {skill}", None, minutes, budget))
        used[index] += minutes

    last = weeks[-1]
    if last["tasks"] and not any(task["type"] == "review" for task in last["tasks"]):
        target = min(15, budget)
        room = budget - sum(task["estimated_minutes"] for task in last["tasks"])
        for task in reversed(last["tasks"]):
            if room >= target:
                break
            spare = task["estimated_minutes"] - 1
            if spare <= 0:
                continue
            take = min(spare, target - max(room, 0))
            task["estimated_minutes"] -= take
            room += take
        if room >= 1:
            last["tasks"].append(_task("review", f"Review what you learned about {skill}", None, min(target, room), budget))
        else:
            last["tasks"][-1]["type"] = "review"
            last["tasks"][-1]["title"] = f"Review what you learned about {skill}"
            last["tasks"][-1]["resource_id"] = None

    allowed = set(by_id)
    plan = validate_plan(
        {"weeks": weeks},
        duration_weeks=duration_weeks,
        hours_per_week=hours_per_week,
        allowed_resource_ids=allowed,
    )
    return plan


def _goal(week_number: int, total: int, skill: str) -> str:
    if week_number == 1:
        return f"Get oriented with {skill}"
    if week_number == total:
        return f"Review {skill} and finish a small project"
    if week_number == 2:
        return f"Go deeper on {skill}"
    return f"Practice {skill}"


def generate_plan_with_retry(
    generate: Callable[[Optional[str]], dict],
    *,
    skill: str,
    duration_weeks: int,
    hours_per_week: int,
    resources: list[dict],
) -> tuple[PlanDraft, str]:
    """
    Call the model up to twice. The second call includes the validation error.
    If both fail, return the template plan.
    """
    allowed = {item["id"] for item in resources}
    error: Optional[str] = None
    for _attempt in (1, 2):
        try:
            raw = generate(error)
        except Exception:
            logger.warning("Plan model call failed", exc_info=True)
            break
        try:
            return (
                validate_plan(
                    raw,
                    duration_weeks=duration_weeks,
                    hours_per_week=hours_per_week,
                    allowed_resource_ids=allowed,
                ),
                "gemini",
            )
        except ValueError as exc:
            error = str(exc)
            logger.info("Plan validation failed: %s", error)
    return (
        build_template_plan(skill, duration_weeks, hours_per_week, resources),
        "template",
    )
