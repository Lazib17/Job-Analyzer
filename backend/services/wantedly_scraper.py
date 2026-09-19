"""
Wantedly job scraper — Playwright-based scraping for startup and engineering roles.
Source: https://www.wantedly.com/
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

WANTEDLY_SEARCH_URL = "https://www.wantedly.com/search?type=projects&q={query}"
WANTEDLY_ENGINEER_URL = "https://www.wantedly.com/search?type=projects&occupation_types%5B%5D=engineer"

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
    "エンジニア",
    "バックエンド",
    "フルスタック",
]

STARTUP_KEYWORDS = ["startup", "スタートアップ", "ベンチャー", "venture"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class WantedlyScraper:
    """Scrapes engineering and startup jobs from Wantedly."""

    def __init__(self):
        self.delay = settings.scrape_delay_seconds

    def _matches_priority(self, title: str, snippet: str = "", query: str = "") -> bool:
        text = f"{title} {snippet} {query}".lower()
        if any(kw in text for kw in PRIORITY_KEYWORDS):
            return True
        if any(kw in text for kw in STARTUP_KEYWORDS):
            return True
        return "engineer" in text

    def _parse_japanese_level(self, text: str) -> str:
        patterns = [
            (r"日本語不問", "Japanese not required"),
            (r"日本語(?:能力)?(?:試験)?\s*N1", "N1"),
            (r"日本語(?:能力)?(?:試験)?\s*N2", "N2"),
            (r"日本語(?:能力)?(?:試験)?\s*N3", "N3"),
            (r"ビジネスレベル", "Business Japanese"),
            (r"日常会話", "Conversational Japanese"),
            (r"no japanese", "Japanese not required"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return ""

    def _parse_remote(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "リモート" in text
            or "在宅" in text
            or "remote" in lowered
            or "work from home" in lowered
        )

    def _parse_visa(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "visa" in lowered
            or "ビザ" in text
            or "sponsorship" in lowered
            or "就労ビザ" in text
        )

    def _extract_requirements(self, text: str) -> list[str]:
        tags = re.findall(
            r"\b(Python|Ruby|Go|Golang|Java|Kotlin|TypeScript|JavaScript|React|"
            r"Node\.js|AWS|Rust|C\+\+|C#|PHP|Rails|Django|FastAPI|DevOps|MLOps|"
            r"Machine Learning|AI|Backend|Full Stack|Startup)\b",
            text,
            re.IGNORECASE,
        )
        return list(dict.fromkeys(t.strip() for t in tags))

    async def _collect_job_links(self, page, query: str, max_results: int) -> list[dict]:
        """Collect project listing links from Wantedly search."""
        search_url = (
            WANTEDLY_SEARCH_URL.format(query=quote_plus(query or "software engineer"))
            if query
            else WANTEDLY_ENGINEER_URL
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(self.delay)

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
                    if (!href.includes('wantedly.com')) return;
                    if (!href.includes('/projects/')) return;
                    if (!text || text.length < 3) return;
                    const clean = href.split('?')[0];
                    if (seen.has(clean)) return;
                    seen.add(clean);
                    results.push({ href: clean, title: text });
                });
                return results;
            }"""
        )

        filtered = [
            item
            for item in raw_links
            if self._matches_priority(item.get("title", ""), query=query)
        ]
        if not filtered:
            filtered = [
                item
                for item in raw_links
                if "engineer" in item.get("title", "").lower()
                or "エンジニア" in item.get("title", "")
            ]

        return filtered[:max_results]

    async def _scrape_job_detail(self, page, href: str, fallback_title: str) -> Optional[ScrapedJob]:
        """Visit a Wantedly project page and extract structured fields."""
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(self.delay * 0.5)

            page_text = await page.inner_text("body")
            title = await page.evaluate(
                """() => {
                    const h1 = document.querySelector('h1');
                    if (h1) return h1.innerText.trim();
                    const t = document.querySelector('[class*="ProjectTitle"], [class*="title"]');
                    return t ? t.innerText.trim() : '';
                }"""
            )
            company = await page.evaluate(
                """() => {
                    const el = document.querySelector(
                        'a[href*="/companies/"], [class*="CompanyName"], [class*="company"]'
                    );
                    return el ? el.innerText.trim() : '';
                }"""
            )

            job_title = title or fallback_title
            if not job_title:
                return None

            location = "Tokyo"
            for loc in (
                "Tokyo",
                "Osaka",
                "Nagoya",
                "Fukuoka",
                "京都",
                "横浜",
                "Remote",
                "リモート",
                "Japan",
                "日本",
            ):
                if loc.lower() in page_text.lower() or loc in page_text:
                    location = loc
                    break

            salary_match = re.search(
                r"(¥[\d.,]+[万円]?|年収\s*\d+万円|\d+万円\s*[〜~\-]\s*\d+万円)",
                page_text,
            )
            salary = salary_match.group(0) if salary_match else ""

            return ScrapedJob(
                job_title=job_title,
                company=company or "Unknown",
                location=location,
                description=page_text[:3000],
                salary=salary,
                requirements=self._extract_requirements(page_text),
                source_platform="wantedly",
                visa_sponsorship=self._parse_visa(page_text),
                japanese_level=self._parse_japanese_level(page_text),
                remote_option=self._parse_remote(page_text),
                job_url=href,
            )
        except Exception as exc:
            logger.warning("Wantedly detail scrape failed for %s: %s", href, exc)
            return None

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape Wantedly jobs matching engineering and startup priorities."""
        logger.info("Wantedly scraping started")
        max_results = max_results or min(15, settings.scrape_max_jobs)
        results: list[ScrapedJob] = []
        query = job_title or "software engineer"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=USER_AGENT,
                locale="ja-JP",
            )
            page = await context.new_page()

            try:
                links = await self._collect_job_links(page, query, max_results)
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

        logger.info("Wantedly jobs found: %d", len(results))
        return results


wantedly_scraper = WantedlyScraper()
