"""
Resume upload and management routes.
"""

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from config import settings
from database import fetch_all, insert_row
from models.resume import ResumeResponse, ResumeUploadResponse
from models.user import UserResponse
from services.resume_parser import extract_resume_text, validate_resume_file
from utils.auth import get_current_user

router = APIRouter(tags=["Resume"])

_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
}


def _resumes_for_user(user_id: str) -> list[dict]:
    return fetch_all(
        "resumes",
        filters={"user_id": user_id},
        order_by="uploaded_at",
        ascending=False,
    )


def _owned_resume_file(file_url: str, user_id: str) -> Path | None:
    """Return the stored CV only if it sits in the upload folder and belongs to this user."""
    if not file_url:
        return None

    upload_root = Path(settings.upload_dir).resolve()
    stored = Path(file_url)
    candidates = [stored] if stored.is_absolute() else [Path.cwd() / stored, upload_root / stored.name]

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not resolved.is_relative_to(upload_root):
            continue
        if not resolved.name.startswith(f"{user_id}_"):
            continue
        if resolved.is_file():
            return resolved
    return None


def _remove_previous_file(previous: dict | None, user_id: str) -> None:
    if not previous:
        return
    path = _owned_resume_file(previous.get("file_url", ""), user_id)
    if not path:
        return
    try:
        path.unlink()
    except OSError:
        pass


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

    # Store in database and drop the previous file so the new CV replaces it.
    user_id = str(current_user.id)
    previous = _resumes_for_user(user_id)
    resume = insert_row(
        "resumes",
        {
            "user_id": user_id,
            "file_url": file_path,
            "extracted_text": extracted_text,
        },
    )
    _remove_previous_file(previous[0] if previous else None, user_id)

    return ResumeUploadResponse(
        message="Resume uploaded and parsed successfully",
        resume=ResumeResponse(**resume),
    )


@router.get("/resume", response_model=ResumeResponse)
async def get_latest_resume(current_user: UserResponse = Depends(get_current_user)):
    """Get the user's most recently uploaded resume."""
    resumes = _resumes_for_user(str(current_user.id))
    if not resumes:
        raise HTTPException(status_code=404, detail="No resume found. Please upload one.")
    return ResumeResponse(**resumes[0])


@router.get("/resume/file")
async def download_latest_resume(current_user: UserResponse = Depends(get_current_user)):
    """Open the original CV file for the current user."""
    user_id = str(current_user.id)
    resumes = _resumes_for_user(user_id)
    if not resumes:
        raise HTTPException(status_code=404, detail="No resume found. Please upload one.")

    path = _owned_resume_file(resumes[0].get("file_url", ""), user_id)
    if path is None:
        raise HTTPException(
            status_code=404,
            detail="Original CV file is no longer available. You can still read the extracted text.",
        )

    suffix = path.suffix.lower()
    disposition = "inline" if suffix == ".pdf" else "attachment"
    return FileResponse(
        path=path,
        media_type=_MEDIA_TYPES.get(suffix, "application/octet-stream"),
        filename=f"cv{suffix}",
        content_disposition_type=disposition,
    )
