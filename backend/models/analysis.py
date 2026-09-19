"""
AI analysis Pydantic models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisBase(BaseModel):
    compatibility_score: int = Field(..., ge=0, le=100)
    missing_skills: Optional[list[str]] = None
    matching_skills: Optional[list[str]] = None
    improvement_suggestions: Optional[str] = None
    ai_reasoning: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    user_id: UUID
    job_id: UUID


class AnalysisResponse(AnalysisBase):
    id: UUID
    user_id: UUID
    job_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AIAnalysisResult(BaseModel):
    """Structured JSON output expected from the AI model."""
    compatibility_score: int = Field(..., ge=0, le=100)
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    improvement_suggestions: str = ""
    explanation: str = ""


class SearchHistoryEntry(BaseModel):
    id: UUID
    user_id: UUID
    job_title: str
    location: str
    results_count: int
    searched_at: datetime
