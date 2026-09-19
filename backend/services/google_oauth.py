"""
Verify Google OAuth access tokens for Sign in with Google.
"""

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


def verify_google_access_token(access_token: str) -> dict:
    """Return Google profile fields (sub, email, name) or raise ValueError."""
    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"access_token": access_token},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Google tokeninfo request failed: %s", exc)
        raise ValueError("Could not reach Google") from exc

    if response.status_code != 200:
        raise ValueError("Invalid Google token")

    info = response.json()
    audience = info.get("aud") or info.get("azp")
    if settings.google_client_id and audience != settings.google_client_id:
        raise ValueError("Google token was not issued for this app")

    email = info.get("email")
    if not email:
        raise ValueError("Google account has no email")

    verified = str(info.get("email_verified", "")).lower()
    if verified not in ("true", "1"):
        raise ValueError("Google email is not verified")

    return {
        "google_id": info.get("sub"),
        "email": email,
        "name": info.get("name") or email.split("@")[0],
    }
