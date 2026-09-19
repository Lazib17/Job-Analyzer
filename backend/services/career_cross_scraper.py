"""
CareerCross job scraper — Playwright-based scraping for bilingual/entry-level Japan jobs.
Source: https://www.careercross.com/
"""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from config import settings
from models.scraped_job import ScrapedJob

logger = logging.getLogger(__name__)

CAREERCROSS_SEARCH_URL = (
    "https://www.careercross.com/en/jobs/search?keywords={keyword}&sort=new"
)
CAREERCROSS_IT_URL = "https://www.careercross.com/en/jobs/search?industry=IT&keywords=engineer"

FRESHMAN_KEYWORDS = [
    "entry",
    "junior",
    "graduate",
    "fresh",
    "no experience",
    "新卒",
    "未経験",
    "second new graduate",
    "trainee",
    "associate",
]

TECH_KEYWORDS = [
    "engineer",
    "developer",
    "software",
    "programmer",
    "IT",
    "SE",
    "system",
    "backend",
    "frontend",
    "data",
    "AI",
    "エンジニア",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class CareerCrossScraper:
    """Scrapes bilingual and entry-level jobs from CareerCross."""

    def __init__(self):
        self.delay = settings.scrape_delay_seconds

    def _is_relevant_job(self, title: str, snippet: str = "") -> bool:
        text = f"{title} {snippet}".lower()
        has_tech = any(kw.lower() in text for kw in TECH_KEYWORDS)
        has_fresh = any(kw.lower() in text for kw in FRESHMAN_KEYWORDS)
        return has_tech and (has_fresh or "engineer" in text or "developer" in text)

    def _parse_japanese_level(self, text: str) -> str:
        patterns = [
            (r"japanese not required", "Japanese not required"),
            (r"no japanese", "Japanese not required"),
            (r"日本語不問", "Japanese not required"),
            (r"jlpt\s*n1", "N1"),
            (r"jlpt\s*n2", "N2"),
            (r"jlpt\s*n3", "N3"),
            (r"business level japanese", "Business Japanese"),
            (r"conversational japanese", "Conversational Japanese"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return ""

    def _parse_salary(self, text: str) -> str:
        match = re.search(
            r"(¥[\d,]+(?:\s*[-–~]\s*¥[\d,]+)?|"
            r"JPY\s*[\d,]+(?:\s*[-–~]\s*[\d,]+)?|"
            r"\d[\d,]*\s*(?:million|万円))",
            text,
            re.IGNORECASE,
        )
        return match.group(0) if match else ""

    def _parse_visa(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "visa sponsorship" in lowered
            or "visa support" in lowered
            or "work visa" in lowered
            or "ビザ" in text
        )

    def _parse_remote(self, text: str) -> bool:
        lowered = text.lower()
        return "remote" in lowered or "work from home" in lowered or "hybrid" in lowered

    async def _collect_listing_links(self, page, keyword: str, max_results: int) -> list[dict]:
        search_url = CAREERCROSS_SEARCH_URL.format(
            keyword=quote_plus(keyword or "entry level engineer")
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
        await asyncio.sleep(self.delay + 1)

        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.8)

        raw_links = await page.evaluate(
            """() => {
                const results = [];
                const seen = new Set();
                document.querySelectorAll('a[href]').forEach((a) => {
                    const href = a.href || '';
                    const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
                    if (!href.includes('careercross.com')) return;
                    if (!href.includes('/jobs/detail') && !href.includes('/job/')) return;
                    const clean = href.split('?')[0];
                    if (seen.has(clean)) return;
                    seen.add(clean);
                    if (!text || text.length < 4) return;
                    results.push({ href: clean, title: text });
                });
                return results;
            }"""
        )

        if not raw_links:
            await page.goto(CAREERCROSS_IT_URL, wait_until="domcontentloaded", timeout=90000)
            await asyncio.sleep(self.delay)
            raw_links = await page.evaluate(
                """() => {
                    const results = [];
                    const seen = new Set();
                    document.querySelectorAll('a[href*="/jobs/detail"]').forEach((a) => {
                        const href = (a.href || '').split('?')[0];
                        const text = (a.innerText || '').trim();
                        if (seen.has(href) || !text) return;
                        seen.add(href);
                        results.push({ href, title: text });
                    });
                    return results;
                }"""
            )

        filtered = [l for l in raw_links if self._is_relevant_job(l.get("title", ""))]
        if not filtered:
            filtered = [
                l for l in raw_links
                if any(kw in l.get("title", "").lower() for kw in ("engineer", "developer", "IT"))
            ]

        return filtered[: max_results * 2]

    async def _scrape_job_detail(self, page, href: str, fallback_title: str) -> Optional[ScrapedJob]:
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(self.delay * 0.5)

            page_text = await page.inner_text("body")
            title = await page.evaluate(
                """() => {
                    const h1 = document.querySelector('h1');
                    if (h1) return h1.innerText.trim();
                    const t = document.querySelector('.job-title, [class*="JobTitle"]');
                    return t ? t.innerText.trim() : '';
                }"""
            )
            company = await page.evaluate(
                """() => {
                    const el = document.querySelector(
                        '.company-name, [class*="Company"], .employer'
                    );
                    return el ? el.innerText.trim() : '';
                }"""
            )

            job_title = title or fallback_title
            if not job_title:
                return None

            location = "Japan"
            for loc in ("Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya", "Fukuoka", "Remote"):
                if loc.lower() in page_text.lower():
                    location = loc
                    break

            requirements: list[str] = []
            for kw in TECH_KEYWORDS + FRESHMAN_KEYWORDS:
                if kw.lower() in page_text.lower() or kw in page_text:
                    if kw not in requirements:
                        requirements.append(kw)

            return ScrapedJob(
                job_title=job_title,
                company=company or "Unknown",
                location=location,
                description=page_text[:3000],
                salary=self._parse_salary(page_text),
                requirements=requirements[:10],
                source_platform="careercross",
                visa_sponsorship=self._parse_visa(page_text),
                japanese_level=self._parse_japanese_level(page_text),
                remote_option=self._parse_remote(page_text),
                job_url=href,
            )
        except Exception as exc:
            logger.warning("CareerCross detail scrape failed for %s: %s", href, exc)
            return None

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape CareerCross entry-level and bilingual tech jobs."""
        logger.info("CareerCross scraping started")
        max_results = max_results or min(15, settings.scrape_max_jobs)
        results: list[ScrapedJob] = []

        keyword = job_title or "entry level engineer"
        if job_title and "entry" not in job_title.lower() and "junior" not in job_title.lower():
            keyword = f"{job_title} entry"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                links = await self._collect_listing_links(page, keyword, max_results)
                for link in links:
                    job = await self._scrape_job_detail(
                        page, link["href"], link.get("title", job_title)
                    )
                    if job and self._is_relevant_job(job.job_title, job.description):
                        results.append(job)
                    elif job and ("engineer" in job.job_title.lower() or "エンジニア" in job.job_title):
                        results.append(job)
                    if len(results) >= max_results:
                        break
            finally:
                await browser.close()

        logger.info("CareerCross jobs found: %d", len(results))
        return results


career_cross_scraper = CareerCrossScraper()
