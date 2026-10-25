"""Profile fields that are not part of the auth response."""

from fastapi import APIRouter, Depends, HTTPException

from database import fetch_one, update_row
from models.learning import JAPANESE_LEVELS, JapaneseLevelResponse, JapaneseLevelUpdate
from models.user import UserResponse
from utils.auth import get_current_user

router = APIRouter(tags=["Profile"])


@router.get("/profile/japanese-level", response_model=JapaneseLevelResponse)
async def get_japanese_level(current_user: UserResponse = Depends(get_current_user)):
    """Return the saved Japanese level, or null if the user has not chosen one."""
    user = fetch_one("users", {"id": str(current_user.id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    level = user.get("japanese_level")
    if level not in JAPANESE_LEVELS:
        level = None
    return JapaneseLevelResponse(japanese_level=level)


@router.put("/profile/japanese-level", response_model=JapaneseLevelResponse)
async def put_japanese_level(
    body: JapaneseLevelUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Save the user's Japanese level on their profile."""
    if body.japanese_level not in JAPANESE_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"japanese_level must be one of: {', '.join(JAPANESE_LEVELS)}",
        )
    try:
        update_row(
            "users",
            str(current_user.id),
            {"japanese_level": body.japanese_level},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not save Japanese level. If this app is using Supabase, "
                "run supabase/migration_japanese_level.sql in the SQL Editor."
            ),
        ) from exc
    return JapaneseLevelResponse(japanese_level=body.japanese_level)
