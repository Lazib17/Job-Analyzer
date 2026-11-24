"""
Career Forum job scraper.
Source: https://careerforum.net/en/event/cfn/companylist/
The public company API includes job titles. Full descriptions come from the public job API.
"""

import logging
import re
from typing import Optional

import httpx

from models.scraped_job import ScrapedJob
from utils.role_match import title_matches

logger = logging.getLogger(__name__)

COMPANIES_URL = "https://careerforum.net/api/public/companies"
JOB_URL = "https://careerforum.net/api/public/jobs/{job_id}"
PUBLIC_JOB_URL = "https://careerforum.net/en/event/{forum}/companylist/{company_id}/{job_id}"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_JAPANESE_LEVELS = (
    ("native", "Native"),
    ("fluent", "Fluent"),
    ("business", "Business Japanese"),
    ("advanced", "Business Japanese"),
    ("intermediate", "Intermediate"),
    ("conversational", "Conversational Japanese"),
    ("daily", "Conversational Japanese"),
    ("basic", "Basic Japanese"),
    ("beginner", "Basic Japanese"),
    ("none", "Japanese not required"),
)

_AREA_NAMES = {
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "aichi": "Aichi",
    "kanagawa": "Kanagawa",
    "fukuoka": "Fukuoka",
    "kyoto": "Kyoto",
    "hyogo": "Hyogo",
    "hokkaido": "Hokkaido",
    "chiba": "Chiba",
    "saitama": "Saitama",
}


class CareerForumScraper:
    """Scrapes bilingual job postings from CareerForum.Net."""

    async def _companies(self, client: httpx.AsyncClient) -> list[dict]:
        companies: list[dict] = []
        page = 1
        while page <= 6:
            response = await client.get(
                COMPANIES_URL,
                params={"eventId": -1, "pageNum": page, "pageSize": 100},
            )
            response.raise_for_status()
            data = response.json().get("data") or {}
            companies.extend(data.get("companyList") or [])
            if page >= int(data.get("pages") or 1):
                break
            page += 1
        return companies

    async def _job_detail(self, client: httpx.AsyncClient, job_id: str) -> dict:
        response = await client.get(JOB_URL.format(job_id=job_id))
        response.raise_for_status()
        return response.json().get("data") or {}

    def _japanese_level(self, languages: list[dict]) -> str:
        chosen = ""
        rank = -1
        for item in languages or []:
            if item.get("languageKey") != "japanese":
                continue
            level_key = str(item.get("languageLevelKey") or "").lower()
            for index, (key, label) in enumerate(_JAPANESE_LEVELS):
                if key in level_key and (len(_JAPANESE_LEVELS) - index) > rank:
                    rank = len(_JAPANESE_LEVELS) - index
                    chosen = label
        return chosen

    def _location(self, recruitment: dict) -> tuple[str, bool]:
        areas = recruitment.get("workAreaList") or []
        names: list[str] = []
        for area in areas:
            key = str(area.get("areaKey") or "")
            name = next((label for token, label in _AREA_NAMES.items() if token in key), "")
            if name and name not in names:
                names.append(name)
        text = str(recruitment.get("workArea") or "")
        remote = bool(re.search(r"remote|在宅|リモート", text, re.IGNORECASE))
        if names:
            return ", ".join(names), remote
        if "日本" in text or "tokyo" in text.lower() or "東京" in text:
            return "Tokyo" if "東京" in text else "Japan", remote
        return "Japan", remote

    def _to_job(self, company: dict, listing: dict, detail: dict) -> ScrapedJob:
        basic = detail.get("jobBasicInfo") or {}
        recruitment = detail.get("recruitmentData") or {}
        qualification = detail.get("applyQualification") or {}
        info = detail.get("companyInfo") or {}
        languages = qualification.get("requiredLanguageList") or []
        location, remote = self._location(recruitment)
        content = str(basic.get("jobContent") or company.get("businessContent") or "")
        if re.search(r"remote|在宅|リモート", content, re.IGNORECASE):
            remote = True
        company_id = listing.get("companyId") or company.get("id")
        job_id = listing.get("jobId")
        forum = listing.get("careerForumKey") or "cfn"
        requirements = [
            f"{item.get('languageKey')}: {item.get('languageLevelKey')}"
            for item in languages
            if item.get("languageKey")
        ]
        return ScrapedJob(
            job_title=str(basic.get("jobName") or listing.get("jobName") or ""),
            company=str(
                info.get("companyName")
                or company.get("dispCompNameEn")
                or company.get("dispCompNameJa")
                or "Unknown"
            ),
            location=location,
            description=content[:3000],
            salary=str(recruitment.get("salary") or "")[:300],
            requirements=requirements[:8],
            source_platform="careerforum",
            visa_sponsorship=bool(re.search(r"visa|ビザ", content, re.IGNORECASE)),
            japanese_level=self._japanese_level(languages),
            remote_option=remote,
            job_url=PUBLIC_JOB_URL.format(forum=forum, company_id=company_id, job_id=job_id),
        )

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        job_titles: Optional[list[str]] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Return Career Forum jobs whose titles match the selected positions."""
        logger.info("Career Forum scraping started")
        selected = job_titles or ([job_title] if job_title else [])
        limit = max_results or 8
        results: list[ScrapedJob] = []

        async with httpx.AsyncClient(
            timeout=30,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        ) as client:
            companies = await self._companies(client)
            matches: list[tuple[dict, dict]] = []
            seen: set[str] = set()
            for company in companies:
                for listing in company.get("jobList") or []:
                    if listing.get("isStopped"):
                        continue
                    job_id = str(listing.get("jobId") or "")
                    name = str(listing.get("jobName") or "")
                    if not job_id or job_id in seen or not title_matches(name, selected):
                        continue
                    seen.add(job_id)
                    matches.append((company, listing))
                    if len(matches) >= limit:
                        break
                if len(matches) >= limit:
                    break

            for company, listing in matches:
                try:
                    detail = await self._job_detail(client, str(listing["jobId"]))
                except Exception as exc:
                    logger.warning("Career Forum detail failed for %s: %s", listing.get("jobId"), exc)
                    detail = {}
                job = self._to_job(company, listing, detail)
                if job.job_title and title_matches(job.job_title, selected):
                    results.append(job)

        logger.info("Career Forum jobs found: %d", len(results))
        return results


career_forum_scraper = CareerForumScraper()
