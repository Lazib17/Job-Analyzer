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
from utils.role_match import search_query, title_matches

logger = logging.getLogger(__name__)

CAREERCROSS_SEARCH_URL = "https://www.careercross.com/en/search?k={keyword}"

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
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(self.delay + 1)
        title = await page.title()
        if "Just a moment" in title or "security verification" in (await page.inner_text("body")).lower():
            logger.warning("CareerCross blocked the browser with a bot check")
            return []

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

        return raw_links[:40]

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
            for loc in (
                "Tokyo",
                "Osaka",
                "Yokohama",
                "Nagoya",
                "Fukuoka",
                "Sapporo",
                "Kobe",
                "Kyoto",
                "Hiroshima",
                "Sendai",
                "Remote",
            ):
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
        job_titles: Optional[list[str]] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape CareerCross jobs whose titles match the selected positions."""
        logger.info("CareerCross scraping started")
        max_results = max_results or min(8, settings.scrape_max_jobs)
        selected = job_titles or ([job_title] if job_title else [])
        results: list[ScrapedJob] = []
        seen: set[str] = set()

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                candidates: list[dict] = []
                for label in selected:
                    links = await self._collect_listing_links(
                        page, search_query(label, "en"), max_results
                    )
                    if not links and "Just a moment" in await page.title():
                        break
                    for link in links:
                        href = link.get("href", "")
                        if href in seen:
                            continue
                        if not title_matches(link.get("title", ""), [label]):
                            continue
                        seen.add(href)
                        candidates.append(link)

                for link in candidates:
                    job = await self._scrape_job_detail(
                        page, link["href"], link.get("title", "")
                    )
                    if job and title_matches(job.job_title, selected):
                        results.append(job)
                    if len(results) >= max_results:
                        break
            finally:
                await browser.close()

        logger.info("CareerCross jobs found: %d", len(results))
        return results


career_cross_scraper = CareerCrossScraper()
