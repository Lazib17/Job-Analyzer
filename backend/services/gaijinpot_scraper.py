"""
GaijinPot job scraper — Playwright-based scraping for foreigner-friendly Japan jobs.
Source: https://jobs.gaijinpot.com/
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

GAIJINPOT_SEARCH_URL = (
    "https://jobs.gaijinpot.com/en/job/search?keyword={keyword}&visa_sponsorship=1"
)
GAIJINPOT_IT_URL = "https://jobs.gaijinpot.com/en/job/category/it-engineer"

TECH_KEYWORDS = [
    "engineer",
    "developer",
    "software",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "ai",
    "ml",
    "data",
    "devops",
    "python",
    "エンジニア",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class GaijinPotScraper:
    """Scrapes foreigner-friendly tech jobs from GaijinPot Jobs."""

    def __init__(self):
        self.delay = settings.scrape_delay_seconds

    def _is_tech_job(self, title: str, snippet: str = "") -> bool:
        text = f"{title} {snippet}".lower()
        return any(kw in text for kw in TECH_KEYWORDS)

    def _is_foreigner_friendly(self, text: str) -> bool:
        lowered = text.lower()
        markers = [
            "visa sponsorship",
            "english",
            "no japanese",
            "japanese not required",
            "foreign national",
            "外国人",
            "英語",
            "日本語不問",
            "ビザサポート",
        ]
        return any(m in lowered or m in text for m in markers)

    def _parse_japanese_level(self, text: str) -> str:
        patterns = [
            (r"japanese not required", "Japanese not required"),
            (r"no japanese", "Japanese not required"),
            (r"日本語不問", "Japanese not required"),
            (r"japanese\s*:\s*none", "Japanese not required"),
            (r"japanese\s*:\s*basic", "Basic Japanese"),
            (r"japanese\s*:\s*conversational", "Conversational Japanese"),
            (r"japanese\s*:\s*business", "Business Japanese"),
            (r"japanese\s*:\s*fluent", "Fluent Japanese"),
            (r"jlpt\s*n1", "N1"),
            (r"jlpt\s*n2", "N2"),
            (r"jlpt\s*n3", "N3"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return ""

    def _parse_remote(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "remote" in lowered
            or "work from home" in lowered
            or "hybrid" in lowered
            or "リモート" in text
            or "在宅" in text
        )

    def _parse_visa(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "visa sponsorship" in lowered
            or "visa support" in lowered
            or "sponsor visa" in lowered
            or "ビザサポート" in text
            or "就労ビザ" in text
        )

    def _parse_salary(self, text: str) -> str:
        match = re.search(
            r"(¥[\d,]+(?:\s*[-–~]\s*¥[\d,]+)?|"
            r"\d[\d,]*\s*(?:JPY|yen)(?:\s*[-–~]\s*\d[\d,]*\s*(?:JPY|yen))?|"
            r"annual salary[:\s]*[\d,]+)",
            text,
            re.IGNORECASE,
        )
        return match.group(0) if match else ""

    def _extract_requirements(self, text: str) -> list[str]:
        tags = re.findall(
            r"\b(Python|Ruby|Go|Java|Kotlin|TypeScript|JavaScript|React|"
            r"Node\.js|AWS|Rust|C\+\+|C#|PHP|Rails|Django|FastAPI|DevOps|"
            r"Machine Learning|AI|English|Visa Sponsorship)\b",
            text,
            re.IGNORECASE,
        )
        return list(dict.fromkeys(t.strip() for t in tags))

    async def _collect_job_links(self, page, keyword: str, max_results: int) -> list[dict]:
        """Collect job listing links from GaijinPot search."""
        search_url = (
            GAIJINPOT_SEARCH_URL.format(keyword=quote_plus(keyword or "engineer"))
            if keyword
            else GAIJINPOT_IT_URL
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
                    if (!href.includes('jobs.gaijinpot.com')) return;
                    if (!href.includes('/job/') || href.includes('/job/search') || href.includes('/job/category')) return;
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
            if self._is_tech_job(item.get("title", ""))
        ]
        if not filtered:
            filtered = raw_links

        return filtered[: max_results * 2]

    async def _scrape_job_detail(self, page, href: str, fallback_title: str) -> Optional[ScrapedJob]:
        """Visit a GaijinPot job detail page."""
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
                        '.company-name, [class*="CompanyName"], a[href*="/company/"]'
                    );
                    return el ? el.innerText.trim() : '';
                }"""
            )

            job_title = title or fallback_title
            if not job_title or not self._is_tech_job(job_title, page_text):
                return None

            if not self._is_foreigner_friendly(page_text):
                return None

            location = "Japan"
            for loc in (
                "Tokyo",
                "Osaka",
                "Kyoto",
                "Nagoya",
                "Fukuoka",
                "Yokohama",
                "Remote",
                "Kanto",
                "Japan",
            ):
                if loc.lower() in page_text.lower():
                    location = loc
                    break

            return ScrapedJob(
                job_title=job_title,
                company=company or "Unknown",
                location=location,
                description=page_text[:3000],
                salary=self._parse_salary(page_text),
                requirements=self._extract_requirements(page_text),
                source_platform="gaijinpot",
                visa_sponsorship=self._parse_visa(page_text),
                japanese_level=self._parse_japanese_level(page_text),
                remote_option=self._parse_remote(page_text),
                job_url=href,
            )
        except Exception as exc:
            logger.warning("GaijinPot detail scrape failed for %s: %s", href, exc)
            return None

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape GaijinPot foreigner-friendly tech jobs."""
        logger.info("GaijinPot scraping started")
        max_results = max_results or min(15, settings.scrape_max_jobs)
        results: list[ScrapedJob] = []
        keyword = job_title or "software engineer"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                links = await self._collect_job_links(page, keyword, max_results)
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

        logger.info("GaijinPot jobs found: %d", len(results))
        return results


gaijinpot_scraper = GaijinPotScraper()
