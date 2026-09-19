"""
Resume-related Pydantic models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ResumeBase(BaseModel):
    file_url: str
    extracted_text: Optional[str] = None


class ResumeCreate(ResumeBase):
    user_id: UUID


class ResumeResponse(ResumeBase):
    id: UUID
    user_id: UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    message: str
    resume: ResumeResponse
