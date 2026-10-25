"""Time-budget checks for generated study plans."""

import pytest

from utils.learning_plan import (
    build_template_plan,
    generate_plan_with_retry,
    validate_plan,
)

RESOURCES = [
    {
        "id": "video:intro",
        "kind": "search_link",
        "title": "Python intro",
        "url": "https://www.youtube.com/results?search_query=python",
        "minutes": 30,
    },
    {
        "id": "video:deep_dive",
        "kind": "search_link",
        "title": "Python deep dive",
        "url": "https://www.youtube.com/results?search_query=python+deep",
        "minutes": 45,
    },
    {
        "id": "video:project",
        "kind": "search_link",
        "title": "Python project",
        "url": "https://www.youtube.com/results?search_query=python+project",
        "minutes": 45,
    },
    {
        "id": "reading:1",
        "kind": "resource",
        "title": "Python tutorial",
        "url": "https://docs.python.org/3/tutorial/index.html",
        "minutes": 40,
    },
]


def _week(minutes: int, resource_id: str | None = "video:intro") -> dict:
    return {
        "goal": "Study Python",
        "tasks": [
            {
                "type": "watch",
                "title": "Watch the intro",
                "resource_id": resource_id,
                "estimated_minutes": minutes,
            }
        ],
    }


def test_week_over_the_time_budget_is_rejected():
    with pytest.raises(ValueError, match="over the 60 minute budget"):
        validate_plan(
            {"weeks": [_week(61)]},
            duration_weeks=1,
            hours_per_week=1,
            allowed_resource_ids={"video:intro"},
        )


def test_week_exactly_at_the_time_budget_passes():
    plan = validate_plan(
        {"weeks": [_week(60)]},
        duration_weeks=1,
        hours_per_week=1,
        allowed_resource_ids={"video:intro"},
    )
    assert sum(task.estimated_minutes for task in plan.weeks[0].tasks) == 60


def test_second_week_over_budget_names_that_week():
    with pytest.raises(ValueError, match="Week 2 totals 121 minutes"):
        validate_plan(
            {"weeks": [_week(60), _week(121)]},
            duration_weeks=2,
            hours_per_week=2,
            allowed_resource_ids={"video:intro"},
        )


def test_wrong_week_count_is_rejected():
    with pytest.raises(ValueError, match="Expected 4 weeks"):
        validate_plan(
            {"weeks": [_week(30), _week(30)]},
            duration_weeks=4,
            hours_per_week=2,
            allowed_resource_ids={"video:intro"},
        )


def test_unknown_resource_id_is_rejected():
    with pytest.raises(ValueError, match="Unknown resource_id made-up"):
        validate_plan(
            {"weeks": [_week(30, "made-up")]},
            duration_weeks=1,
            hours_per_week=2,
            allowed_resource_ids={"video:intro"},
        )


def test_template_stays_inside_the_weekly_budget():
    for weeks, hours in ((1, 1), (2, 1), (4, 3), (12, 5), (24, 2)):
        plan = build_template_plan("Python", weeks, hours, RESOURCES)
        assert len(plan.weeks) == weeks
        budget = hours * 60
        for week in plan.weeks:
            assert week.tasks
            assert sum(task.estimated_minutes for task in week.tasks) <= budget
        assert any(task.type == "review" for task in plan.weeks[-1].tasks)


def test_invalid_model_output_retries_once_then_uses_template():
    calls = []

    def generate(error):
        calls.append(error)
        if len(calls) == 1:
            return {"weeks": [_week(90), _week(90)]}
        return {"weeks": []}

    plan, source = generate_plan_with_retry(
        generate,
        skill="Python",
        duration_weeks=2,
        hours_per_week=1,
        resources=RESOURCES,
    )
    assert source == "template"
    assert calls[1] and "budget" in calls[1]
    assert len(plan.weeks) == 2
    assert all(
        sum(task.estimated_minutes for task in week.tasks) <= 60
        for week in plan.weeks
    )


def test_second_model_attempt_can_succeed():
    calls = []

    def generate(error):
        calls.append(error)
        if error is None:
            return {"weeks": [_week(90)]}
        return {"weeks": [_week(45)]}

    plan, source = generate_plan_with_retry(
        generate,
        skill="Python",
        duration_weeks=1,
        hours_per_week=1,
        resources=RESOURCES,
    )
    assert source == "gemini"
    assert len(calls) == 2
    assert plan.weeks[0].tasks[0].estimated_minutes == 45
