"""
Job-related Pydantic models.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


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


class JobSearchRequest(BaseModel):
    """User preferences for LinkedIn job search."""
    job_title: str = Field(..., min_length=1, description="Desired job title")
    location: str = Field(default="Remote", description="Job location")
    experience_level: Optional[str] = Field(
        default=None, description="e.g. entry, mid, senior"
    )
    remote_only: bool = False
    max_results: int = Field(default=25, ge=1, le=50)
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
