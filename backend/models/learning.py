"""Models for the Improve Your Skills endpoints."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


JAPANESE_LEVELS = (
    "None",
    "N5",
    "N4",
    "N3",
    "N2",
    "N1",
    "Native/Fluent",
    "Not sure",
)


class JapaneseLevelUpdate(BaseModel):
    japanese_level: str = Field(..., description="Self-reported Japanese level")


class JapaneseLevelResponse(BaseModel):
    japanese_level: Optional[str] = None


class LearningSkillResponse(BaseModel):
    skill: str
    rank: int
    jobs_missing_count: int
    total_jobs: int
    demand_percent: int
    tier: str


class LearningSkillsResponse(BaseModel):
    total_jobs: int
    japanese_level: Optional[str] = None
    skills: list[LearningSkillResponse]


class LearningVideoResponse(BaseModel):
    kind: str
    stage: str
    videoId: Optional[str] = None
    title: str
    channel: Optional[str] = None
    duration: Optional[str] = None
    views: Optional[int] = None
    publishedAt: Optional[str] = None
    thumbnail: Optional[str] = None
    url: str


class LearningReadingResponse(BaseModel):
    kind: str
    title: str
    url: str
    source: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_minutes: Optional[int] = None


class LearningResourcesResponse(BaseModel):
    skill: str
    videos: list[LearningVideoResponse]
    readings: list[LearningReadingResponse]


_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


class PlanCreateRequest(BaseModel):
    skill: str = Field(min_length=1, max_length=120)
    duration_weeks: int = Field(ge=1, le=24)
    hours_per_week: int = Field(ge=1, le=20)
    start_date: Optional[date] = None
    study_days: Optional[list[str]] = None

    @field_validator("study_days")
    @classmethod
    def _study_days(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned: list[str] = []
        for day in value:
            key = day.strip().lower()[:3]
            if key not in _WEEKDAYS:
                raise ValueError("study_days must use weekday names such as mon or friday")
            if key not in cleaned:
                cleaned.append(key)
        return cleaned


class TaskProgressRequest(BaseModel):
    done: bool


class PlanTaskResponse(BaseModel):
    id: str
    type: str
    title: str
    resource_id: Optional[str] = None
    resource: Optional[dict] = None
    estimated_minutes: int
    done: bool


class PlanWeekResponse(BaseModel):
    week_number: int
    goal: str
    tasks: list[PlanTaskResponse]


class PlanProgressResponse(BaseModel):
    done: int
    total: int


class LearningPlanResponse(BaseModel):
    id: str
    skill: str
    duration_weeks: int
    hours_per_week: int
    start_date: Optional[str] = None
    study_days: Optional[list[str]] = None
    japanese_level: Optional[str] = None
    source: str
    created_at: Optional[str] = None
    progress: PlanProgressResponse
    weeks: list[PlanWeekResponse]


class LearningPlanSummaryResponse(BaseModel):
    id: str
    skill: str
    duration_weeks: int
    hours_per_week: int
    start_date: Optional[str] = None
    source: str
    created_at: Optional[str] = None
    progress: PlanProgressResponse
