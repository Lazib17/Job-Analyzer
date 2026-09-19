"""
LinkedIn job scraper using guest API (httpx) with optional Playwright fallback.
"""

import asyncio
import logging
import random
import re
from html import unescape
from typing import Optional
from urllib.parse import quote_plus

import httpx
from playwright.async_api import Browser, Page, async_playwright

from config import settings
from models.job import JobBase

logger = logging.getLogger(__name__)

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"
GUEST_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
GUEST_JOB_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class LinkedInScraper:
    """Scrapes LinkedIn job listings via guest API or Playwright fallback."""

    def __init__(self):
        self.max_retries = settings.scrape_max_retries
        self.delay = settings.scrape_delay_seconds
        self.max_jobs = settings.scrape_max_jobs

    async def _random_delay(self, multiplier: float = 1.0) -> None:
        wait = self.delay * multiplier * random.uniform(0.5, 1.2)
        await asyncio.sleep(wait)

    def _build_search_params(
        self,
        job_title: str,
        location: str,
        remote_only: bool = False,
        experience_level: Optional[str] = None,
    ) -> dict[str, str]:
        params = {
            "keywords": job_title,
            "location": location,
            "start": "0",
        }
        if remote_only:
            params["f_WT"] = "2"
        exp_map = {"entry": "2", "associate": "3", "mid": "4", "senior": "4", "director": "5"}
        if experience_level and experience_level.lower() in exp_map:
            params["f_E"] = exp_map[experience_level.lower()]
        return params

    def _clean_text(self, text: str) -> str:
        return " ".join(unescape(text).split())

    def _parse_search_html(self, html: str, max_results: int) -> list[dict]:
        """Parse job cards from LinkedIn guest search HTML response."""
        jobs: list[dict] = []
        job_ids = re.findall(r'urn:li:jobPosting:(\d+)', html)
        seen_ids: set[str] = set()

        for job_id in job_ids:
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            marker = f'urn:li:jobPosting:{job_id}'
            pos = html.find(marker)
            if pos == -1:
                continue
            chunk = html[pos : pos + 5000]

            title_match = re.search(
                r'base-search-card__title[^>]*>[\s\S]*?([^<\n][^<]{2,}?)\s*</h3>',
                chunk,
                re.IGNORECASE,
            )
            if not title_match:
                title_match = re.search(
                    r'class="sr-only"[^>]*>[\s\S]*?([^<\n][^<]{2,}?)\s*</span>',
                    chunk,
                    re.IGNORECASE,
                )

            company_match = re.search(
                r'base-search-card__subtitle[\s\S]*?>([^<]{2,}?)</a>',
                chunk,
                re.IGNORECASE,
            )
            if not company_match:
                company_match = re.search(
                    r'base-search-card__subtitle[^>]*>[\s\S]*?>([^<]{2,}?)</h4>',
                    chunk,
                    re.IGNORECASE,
                )

            location_match = re.search(
                r'job-search-card__location[^>]*>[\s\S]*?([^<\n][^<]{1,}?)\s*</span>',
                chunk,
                re.IGNORECASE,
            )
            link_match = re.search(r'href="(https://[^"]+/jobs/view/[^"?]+)', chunk)

            title = self._clean_text(title_match.group(1)) if title_match else ""
            company = self._clean_text(company_match.group(1)) if company_match else ""
            if not title:
                continue
            if not company:
                company = "Unknown"

            job_url = link_match.group(1) if link_match else f"https://www.linkedin.com/jobs/view/{job_id}"
            jobs.append(
                {
                    "job_id": job_id,
                    "job_title": title,
                    "company": company,
                    "location": self._clean_text(location_match.group(1)) if location_match else "",
                    "job_url": job_url,
                }
            )
            if len(jobs) >= max_results:
                break
        return jobs

    def _parse_job_detail_html(self, html: str) -> dict:
        """Parse description and salary from job detail HTML."""
        details: dict = {"description": "", "requirements": "", "salary": None}

        desc_match = re.search(
            r'class="show-more-less-html__markup[^"]*"[^>]*>([\s\S]*?)</div>',
            html,
            re.IGNORECASE,
        )
        if desc_match:
            raw = re.sub(r"<[^>]+>", "\n", desc_match.group(1))
            details["description"] = unescape(re.sub(r"\n{3,}", "\n\n", raw)).strip()

        salary_match = re.search(
            r'salary[^>]*>([^<]*[$£€][^<]*)', html, re.IGNORECASE
        )
        if salary_match:
            details["salary"] = unescape(salary_match.group(1).strip())

        if details["description"]:
            details["requirements"] = self._extract_requirements(details["description"])
        return details

    def _extract_requirements(self, description: str) -> str:
        patterns = [
            r"(?:requirements?|qualifications?|what you.ll need|must have)[:\s]*([\s\S]*?)(?:\n\n|\Z)",
            r"(?:minimum qualifications?)[:\s]*([\s\S]*?)(?:\n\n|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:2000]
        return description[:1500]

    async def _fetch_job_details(self, client: httpx.AsyncClient, job_id: str) -> dict:
        if not job_id:
            return {"description": "", "requirements": "", "salary": None}
        try:
            url = GUEST_JOB_URL.format(job_id=job_id)
            response = await client.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return self._parse_job_detail_html(response.text)
        except Exception as exc:
            logger.warning("Failed to fetch details for job %s: %s", job_id, exc)
            return {"description": "", "requirements": "", "salary": None}

    async def _scrape_with_guest_api(
        self,
        job_title: str,
        location: str,
        remote_only: bool,
        experience_level: Optional[str],
        max_results: int,
    ) -> list[JobBase]:
        """Scrape jobs using LinkedIn's public guest API (no browser needed)."""
        params = self._build_search_params(job_title, location, remote_only, experience_level)
        results: list[JobBase] = []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(GUEST_SEARCH_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()

            cards = self._parse_search_html(response.text, max_results)
            logger.info("Guest API found %d job cards", len(cards))

            for i, card in enumerate(cards):
                details = await self._fetch_job_details(client, card.get("job_id", ""))
                results.append(
                    JobBase(
                        job_title=card["job_title"],
                        company=card["company"],
                        location=card.get("location"),
                        description=details.get("description"),
                        salary=details.get("salary"),
                        requirements=details.get("requirements"),
                        job_url=card.get("job_url"),
                    )
                )
                logger.info(
                    "Scraped job %d/%d: %s at %s",
                    i + 1, len(cards), card["job_title"], card["company"],
                )
                await self._random_delay(0.3)

        return results

    async def _scrape_with_browser(
        self,
        job_title: str,
        location: str,
        remote_only: bool,
        experience_level: Optional[str],
        max_results: int,
    ) -> list[JobBase]:
        """Playwright fallback when guest API is unavailable."""
        params = self._build_search_params(job_title, location, remote_only, experience_level)
        query = "&".join(f"{k}={quote_plus(v)}" for k, v in params.items() if k != "start")
        search_url = LINKEDIN_JOBS_URL + "?" + query
        results: list[JobBase] = []

        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=HEADERS["User-Agent"])
            page = await context.new_page()
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await self._random_delay()
            cards = await self._extract_job_cards_playwright(page, max_results)
            for card in cards:
                details = await self._extract_job_details_playwright(page, card.get("job_url", ""))
                results.append(JobBase(**{**card, **details}))
            await browser.close()
        return results

    async def _extract_job_cards_playwright(self, page: Page, max_results: int) -> list[dict]:
        await page.wait_for_selector("ul.jobs-search__results-list li, div.base-card", timeout=20000)
        cards = await page.query_selector_all("ul.jobs-search__results-list li, div.base-card")
        jobs: list[dict] = []
        for card in cards[:max_results]:
            try:
                title_el = await card.query_selector(".base-search-card__title")
                company_el = await card.query_selector(".base-search-card__subtitle")
                location_el = await card.query_selector(".job-search-card__location")
                link_el = await card.query_selector("a[href*='/jobs/view/']")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                location = (await location_el.inner_text()).strip() if location_el else ""
                href = await link_el.get_attribute("href") if link_el else ""
                if title and company:
                    jobs.append({
                        "job_title": title, "company": company,
                        "location": location, "job_url": href.split("?")[0] if href else "",
                    })
            except Exception:
                continue
        return jobs

    async def _extract_job_details_playwright(self, page: Page, job_url: str) -> dict:
        details: dict = {"description": "", "requirements": "", "salary": None}
        if not job_url:
            return details
        try:
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            desc_el = await page.query_selector(".show-more-less-html__markup")
            if desc_el:
                details["description"] = (await desc_el.inner_text()).strip()
                details["requirements"] = self._extract_requirements(details["description"])
        except Exception as exc:
            logger.warning("Playwright detail fetch failed: %s", exc)
        return details

    async def search_jobs(
        self,
        job_title: str,
        location: str = "Remote",
        remote_only: bool = False,
        experience_level: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[JobBase]:
        """Search LinkedIn jobs using the public guest API."""
        max_results = max_results or self.max_jobs
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Scrape attempt %d/%d for '%s' in '%s'",
                    attempt, self.max_retries, job_title, location,
                )
                jobs = await self._scrape_with_guest_api(
                    job_title, location, remote_only, experience_level, max_results
                )
                if jobs:
                    return jobs
                logger.warning("Guest API returned 0 jobs on attempt %d", attempt)
            except Exception as exc:
                last_error = exc
                logger.error("Guest API attempt %d failed: %s", attempt, exc)

            if attempt < self.max_retries:
                await asyncio.sleep(self.delay * attempt)

        if last_error:
            raise RuntimeError(
                f"LinkedIn job search failed: {last_error}"
            )
        raise RuntimeError(
            "No jobs found for that search. Try different keywords or location."
        )


linkedin_scraper = LinkedInScraper()
