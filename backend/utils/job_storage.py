"""
Convert standardized scraped jobs into Supabase insert payloads.
"""

import json

from models.scraped_job import ScrapedJob


def scraped_job_to_db_row(job: ScrapedJob, user_id: str) -> dict:
    """Map ScrapedJob to the jobs table insert dictionary."""
    requirements_value: str | None = None
    if job.requirements:
        requirements_value = json.dumps(job.requirements, ensure_ascii=False)

    row = {
        "user_id": user_id,
        "job_title": job.job_title,
        "company": job.company,
        "location": job.location or None,
        "description": job.description or None,
        "salary": job.salary or None,
        "requirements": requirements_value,
        "job_url": job.job_url or None,
        "source_platform": job.source_platform,
        "visa_sponsorship": job.visa_sponsorship,
        "japanese_level": job.japanese_level or None,
        "remote_option": job.remote_option,
    }
    return row
