"""
Application configuration loaded from environment variables.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Job Analyzer backend."""

    # App
    app_name: str = "LinkedIn Job Analyzer"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # Google AI Studio (Gemini)
    google_api_key: str = ""
    google_model: str = "gemini-1.5-flash"

    # Google OAuth (Sign in with Google)
    google_client_id: str = ""

    # LinkedIn scraping
    linkedin_email: str = ""
    linkedin_password: str = ""
    scrape_max_retries: int = 3
    scrape_delay_seconds: float = 2.0
    scrape_max_jobs: int = 25

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
