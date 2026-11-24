"""
Job-related Pydantic models.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class JobBase(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    salary: Optional[str] = None
    requirements: Optional[str] = None
    job_url: Optional[str] = None


class JobCreate(JobBase):
    user_id: UUID


class JobResponse(JobBase):
    id: UUID
    user_id: UUID
    is_favorite: bool = False
    created_at: datetime
    source_platform: Optional[str] = None
    visa_sponsorship: Optional[bool] = None
    japanese_level: Optional[str] = None
    remote_option: Optional[bool] = None

    class Config:
        from_attributes = True


JAPANESE_SEARCH_LEVELS = (
    "Native",
    "Business level",
    "Intermediate",
    "Daily conversation level",
    "No Japanese",
)


WORK_ARRANGEMENTS = ("Any", "Remote", "On-site", "Hybrid")


class JobSearchRequest(BaseModel):
    """Positions and filters for a Japan job-board search."""
    job_title: str = ""
    job_titles: list[str] = Field(default_factory=list, max_length=4)
    location: str = Field(default="Any", description="Remote, On-site, Hybrid, or Any")
    city: str = Field(default="Any", description="Japanese city, or Any")
    experience_level: Optional[str] = Field(
        default=None, description="e.g. entry, mid, senior"
    )
    remote_only: bool = False
    max_results: int = Field(default=8, ge=1, le=50)
    japanese_level: str = Field(
        default="No Japanese",
        description="Highest Japanese level the user can work in",
    )

    @field_validator("japanese_level")
    @classmethod
    def _normalize_japanese_level(cls, value: str) -> str:
        cleaned = value.strip()
        allowed = {item.lower(): item for item in JAPANESE_SEARCH_LEVELS}
        match = allowed.get(cleaned.lower())
        if match is None:
            raise ValueError(
                "japanese_level must be one of: " + ", ".join(JAPANESE_SEARCH_LEVELS)
            )
        return match

    @field_validator("location")
    @classmethod
    def _normalize_location(cls, value: str) -> str:
        cleaned = value.strip()
        allowed = {item.lower(): item for item in WORK_ARRANGEMENTS}
        match = allowed.get(cleaned.lower())
        if match is None:
            raise ValueError(
                "location must be one of: " + ", ".join(WORK_ARRANGEMENTS)
            )
        return match

    @field_validator("city")
    @classmethod
    def _normalize_city(cls, value: str) -> str:
        from utils.city_match import CITY_NAMES

        cleaned = value.strip()
        allowed = {item.lower(): item for item in CITY_NAMES}
        match = allowed.get(cleaned.lower())
        if match is None:
            raise ValueError("city must be one of: " + ", ".join(CITY_NAMES))
        return match

    @model_validator(mode="after")
    def _normalize_titles(self):
        from utils.role_match import ROLE_BY_LABEL

        raw = [item.strip() for item in self.job_titles if item and item.strip()]
        if not raw and self.job_title.strip():
            raw = [part.strip() for part in self.job_title.split(",") if part.strip()]
        chosen: list[str] = []
        for item in raw:
            match = ROLE_BY_LABEL.get(item)
            if match is None:
                folded = {label.lower(): label for label in ROLE_BY_LABEL}
                match_label = folded.get(item.lower())
                if match_label is None:
                    raise ValueError("Choose a position from the list")
                item = match_label
            else:
                item = match["label"]
            if item not in chosen:
                chosen.append(item)
        if not chosen:
            raise ValueError("Choose at least one position")
        if len(chosen) > 4:
            raise ValueError("Choose up to 4 positions")
        self.job_titles = chosen
        self.job_title = ", ".join(chosen)
        return self


class JobWithAnalysis(JobResponse):
    """Job enriched with AI analysis data."""
    compatibility_score: Optional[int] = None
    missing_skills: Optional[list[str]] = None
    matching_skills: Optional[list[str]] = None
    improvement_suggestions: Optional[str] = None
    ai_reasoning: Optional[str] = None
    analysis_id: Optional[UUID] = None


class JobTranslateRequest(BaseModel):
    language: Literal["en", "ja"]


class JobTranslationResponse(BaseModel):
    language: Literal["en", "ja"]
    job_title: str = ""
    company: str = ""
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    ai_reasoning: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    matching_skills: list[str] = []
    missing_skills: list[str] = []


class JobFilterParams(BaseModel):
    min_score: Optional[int] = Field(default=None, ge=0, le=100)
    favorites_only: bool = False
    search_query: Optional[str] = None
