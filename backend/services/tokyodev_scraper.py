"""
TokyoDev job scraper — Playwright-based scraping for English-friendly Japan tech jobs.
Source: https://www.tokyodev.com/jobs
"""

import asyncio
import logging
import re
from typing import Optional

from playwright.async_api import async_playwright

from config import settings
from models.scraped_job import ScrapedJob

logger = logging.getLogger(__name__)

TOKYODEV_JOBS_URL = "https://www.tokyodev.com/jobs"

PRIORITY_KEYWORDS = [
    "software engineer",
    "backend engineer",
    "back-end engineer",
    "full stack",
    "fullstack",
    "full-stack",
    "ai engineer",
    "ml engineer",
    "machine learning",
    "ai/ml",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class TokyoDevScraper:
    """Scrapes engineering jobs from TokyoDev."""

    def __init__(self):
        self.delay = settings.scrape_delay_seconds

    def _matches_priority(self, title: str, query: str = "") -> bool:
        text = f"{title} {query}".lower()
        return any(kw in text for kw in PRIORITY_KEYWORDS)

    def _parse_japanese_level(self, text: str) -> str:
        levels = [
            "No Japanese required",
            "Conversational Japanese",
            "Business Japanese",
            "Fluent Japanese",
            "Basic Japanese",
        ]
        for level in levels:
            if level.lower() in text.lower():
                return level
        return ""

    def _parse_remote(self, text: str) -> bool:
        lowered = text.lower()
        return "fully remote" in lowered or "partially remote" in lowered

    def _parse_visa(self, text: str) -> bool:
        lowered = text.lower()
        return "apply from abroad" in lowered or "visa sponsorship" in lowered

    def _extract_tech_stack(self, text: str) -> list[str]:
        tags = re.findall(
            r"\b(Python|Ruby|Go|Golang|Java|Kotlin|TypeScript|JavaScript|React|"
            r"Node\.js|AWS|Rust|C\+\+|C#|PHP|Rails|Django|FastAPI|DevOps|MLOps|"
            r"Machine Learning|Generative AI|Backend|Full Stack)\b",
            text,
            re.IGNORECASE,
        )
        return list(dict.fromkeys(t.strip() for t in tags))

    async def _collect_job_links(self, page, max_results: int) -> list[dict]:
        """Collect job listing links from the TokyoDev jobs index."""
        await page.goto(TOKYODEV_JOBS_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(self.delay)

        # Scroll to load more listings
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
                    if (!href.includes('tokyodev.com')) return;
                    if (!text || text.length < 5) return;
                    if (href.includes('/companies/') && href.includes('/jobs/')) {
                        if (!seen.has(href)) {
                            seen.add(href);
                            results.push({ href, title: text });
                        }
                    }
                });
                return results;
            }"""
        )

        filtered = []
        for item in raw_links:
            title = item.get("title", "")
            if self._matches_priority(title):
                filtered.append(item)
            if len(filtered) >= max_results:
                break

        # Fallback: include any engineer-related links if priority filter is too strict
        if not filtered:
            for item in raw_links:
                if "engineer" in item.get("title", "").lower():
                    filtered.append(item)
                if len(filtered) >= max_results:
                    break

        return filtered[:max_results]

    async def _scrape_job_detail(self, page, href: str, fallback_title: str) -> Optional[ScrapedJob]:
        """Visit a TokyoDev job page and extract structured fields."""
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(self.delay * 0.5)

            page_text = await page.inner_text("body")
            title = await page.evaluate(
                """() => {
                    const h1 = document.querySelector('h1');
                    return h1 ? h1.innerText.trim() : '';
                }"""
            )
            company = await page.evaluate(
                """() => {
                    const el = document.querySelector('a[href*="/companies/"]');
                    return el ? el.innerText.trim() : '';
                }"""
            )

            job_title = title or fallback_title
            if not job_title:
                return None

            salary_match = re.search(r"¥[\d.,]+M?\s*~\s*¥[\d.,]+M?", page_text)
            salary = salary_match.group(0) if salary_match else ""

            location = "Tokyo"
            for loc in ("Tokyo", "Osaka", "Nagoya", "Fukuoka", "Remote", "Japan"):
                if loc.lower() in page_text.lower():
                    location = loc
                    break

            tech_stack = self._extract_tech_stack(page_text)
            description = page_text[:3000]

            return ScrapedJob(
                job_title=job_title,
                company=company or "Unknown",
                location=location,
                description=description,
                salary=salary,
                requirements=tech_stack,
                source_platform="tokyodev",
                visa_sponsorship=self._parse_visa(page_text),
                japanese_level=self._parse_japanese_level(page_text),
                remote_option=self._parse_remote(page_text),
                job_url=href,
            )
        except Exception as exc:
            logger.warning("TokyoDev detail scrape failed for %s: %s", href, exc)
            return None

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape TokyoDev jobs matching engineering priorities."""
        logger.info("TokyoDev scraping started")
        max_results = max_results or min(15, settings.scrape_max_jobs)
        results: list[ScrapedJob] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                links = await self._collect_job_links(page, max_results)
                for link in links:
                    job = await self._scrape_job_detail(
                        page, link["href"], link.get("title", job_title)
                    )
                    if job:
                        results.append(job)
                    if len(results) >= max_results:
                        break
            finally:
                await browser.close()

        logger.info("TokyoDev jobs found: %d", len(results))
        return results


tokyodev_scraper = TokyoDevScraper()
