"""
Standardized scraped job format used across all job platforms.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ScrapedJob(BaseModel):
    """Unified job output from any scraper source."""

    job_title: str
    company: str
    location: str = ""
    description: str = ""
    salary: str = ""
    requirements: list[str] = Field(default_factory=list)
    source_platform: str
    visa_sponsorship: bool = False
    japanese_level: str = ""
    remote_option: bool = False
    job_url: str = ""
