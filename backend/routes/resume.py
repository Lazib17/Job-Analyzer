"""
Resume upload and management routes.
"""

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from config import settings
from database import fetch_all, insert_row
from models.resume import ResumeResponse, ResumeUploadResponse
from models.user import UserResponse
from services.resume_parser import extract_resume_text, validate_resume_file
from utils.auth import get_current_user

router = APIRouter(tags=["Resume"])


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Upload a CV (PDF/DOCX), extract text, and save to Supabase.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        validate_resume_file(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Save file locally
    ext = Path(file.filename).suffix.lower()
    unique_name = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {settings.max_upload_size_mb}MB.",
        )

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Extract text from resume
    try:
        extracted_text = extract_resume_text(file_path)
    except Exception as exc:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {exc}") from exc

    # Store in database
    resume = insert_row(
        "resumes",
        {
            "user_id": str(current_user.id),
            "file_url": file_path,
            "extracted_text": extracted_text,
        },
    )

    return ResumeUploadResponse(
        message="Resume uploaded and parsed successfully",
        resume=ResumeResponse(**resume),
    )


@router.get("/resume", response_model=ResumeResponse)
async def get_latest_resume(current_user: UserResponse = Depends(get_current_user)):
    """Get the user's most recently uploaded resume."""
    resumes = fetch_all(
        "resumes",
        filters={"user_id": str(current_user.id)},
        order_by="uploaded_at",
        ascending=False,
    )
    if not resumes:
        raise HTTPException(status_code=404, detail="No resume found. Please upload one.")
    return ResumeResponse(**resumes[0])
