"""
Authentication routes — register, login, and profile.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from database import fetch_one, insert_row, update_row
from models.user import GoogleAuthRequest, Token, UserCreate, UserLogin, UserResponse
from services.google_oauth import verify_google_access_token
from utils.auth import create_access_token, get_current_user, hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _db_error(detail: str = "Database unavailable. Please try again later.") -> HTTPException:
    return HTTPException(status_code=503, detail=detail)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user account."""
    try:
        existing = fetch_one("users", {"email": user_data.email})
    except Exception as exc:
        logger.exception("Database error checking existing user")
        raise _db_error() from exc

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = insert_row(
            "users",
            {
                "name": user_data.name,
                "email": user_data.email,
                "password_hash": hash_password(user_data.password),
            },
        )
    except Exception as exc:
        logger.exception("Database error creating user")
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(status_code=400, detail="Email already registered") from exc
        raise _db_error() from exc

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return Token(
        access_token=token,
        user=UserResponse(**user),
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT token."""
    try:
        user = fetch_one("users", {"email": credentials.email})
    except Exception as exc:
        logger.exception("Database error during login")
        raise _db_error() from exc

    if not user or not user.get("password_hash") or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return Token(
        access_token=token,
        user=UserResponse(**user),
    )


@router.post("/google", response_model=Token)
async def google_login(body: GoogleAuthRequest):
    """Sign in or register with a Google access token; issue the same JWT as password login."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")

    try:
        profile = verify_google_access_token(body.access_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    google_id = profile["google_id"]
    email = profile["email"]
    name = profile["name"]

    try:
        user = fetch_one("users", {"google_id": google_id}) if google_id else None
        if not user:
            user = fetch_one("users", {"email": email})
    except Exception as exc:
        logger.exception("Database error looking up Google user")
        raise _db_error() from exc

    try:
        if user:
            existing_google = user.get("google_id")
            if existing_google and existing_google != google_id:
                raise HTTPException(
                    status_code=400,
                    detail="This email is already linked to a different Google account",
                )
            if not existing_google and google_id:
                user = update_row("users", str(user["id"]), {"google_id": google_id}) or user
                user["google_id"] = google_id
        else:
            user = insert_row(
                "users",
                {
                    "name": name,
                    "email": email,
                    "password_hash": None,
                    "google_id": google_id,
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Database error creating Google user")
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(status_code=400, detail="Email already registered") from exc
        raise _db_error() from exc

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return Token(
        access_token=token,
        user=UserResponse(**user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
