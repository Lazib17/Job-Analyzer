"""
Mynavi job scraper — Playwright-based scraping for new grad and entry-level roles.
Sources: https://job.mynavi.jp/ (新卒) and https://tenshoku.mynavi.jp/ (未経験)
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

MYNAVI_NEWGRAD_SEARCH = "https://job.mynavi.jp/26/pc/search/query.html?QKeywords={keyword}"
MYNAVI_ENTRY_SEARCH = "https://tenshoku.mynavi.jp/list/kw{keyword}/"
MYNAVI_ENGINEER_HUB = "https://tenshoku.mynavi.jp/engineer/"

FRESHMAN_KEYWORDS = [
    "新卒",
    "第二新卒",
    "未経験",
    "entry",
    "junior",
    "graduate",
    "fresh",
    "初任給",
    "新入社員",
]

TECH_KEYWORDS = [
    "エンジニア",
    "engineer",
    "developer",
    "IT",
    "システム",
    "SE",
    "プログラマ",
    "Python",
    "AI",
    "データ",
    "インフラ",
    "web",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class MynaviScraper:
    """Scrapes entry-level and new-grad jobs from Mynavi."""

    def __init__(self):
        self.delay = settings.scrape_delay_seconds

    def _is_relevant_job(self, title: str, snippet: str = "") -> bool:
        text = f"{title} {snippet}"
        has_tech = any(kw.lower() in text.lower() or kw in text for kw in TECH_KEYWORDS)
        has_fresh = any(kw in text for kw in FRESHMAN_KEYWORDS) or any(
            kw in text.lower() for kw in ("entry", "junior", "graduate", "fresh")
        )
        return has_tech and (has_fresh or "エンジニア" in text or "engineer" in text.lower())

    def _parse_japanese_level(self, text: str) -> str:
        patterns = [
            (r"日本語(?:能力)?(?:試験)?\s*N1", "N1"),
            (r"日本語(?:能力)?(?:試験)?\s*N2", "N2"),
            (r"日本語(?:能力)?(?:試験)?\s*N3", "N3"),
            (r"日本語不問", "Japanese not required"),
            (r"ビジネスレベル", "Business Japanese"),
            (r"日常会話", "Conversational Japanese"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return ""

    def _parse_salary(self, text: str) -> str:
        match = re.search(
            r"(\d{3,4})[万円]?\s*[〜~\-－]\s*(\d{3,4})[万円]?",
            text,
        )
        if match:
            return f"{match.group(1)}万円 ~ {match.group(2)}万円"
        single = re.search(r"(初任給|年収|月収)\s*(\d{3,4})[万円]?", text)
        if single:
            return f"{single.group(1)} {single.group(2)}万円"
        return ""

    async def _collect_listing_links(self, page, keyword: str, max_results: int) -> list[dict]:
        """Collect job listing URLs from Mynavi new-grad and entry-level search."""
        search_terms = [
            MYNAVI_ENTRY_SEARCH.format(keyword=quote_plus(keyword or "未経験 エンジニア")),
            MYNAVI_NEWGRAD_SEARCH.format(keyword=quote_plus(keyword or "エンジニア")),
        ]

        all_links: list[dict] = []
        seen: set[str] = set()

        for search_url in search_terms:
            if len(all_links) >= max_results:
                break
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(self.delay)

                body_text = await page.inner_text("body")
                if "該当する求人" in body_text and "0件" in body_text:
                    continue

                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(0.8)

                links = await page.evaluate(
                    """() => {
                        const results = [];
                        const seen = new Set();
                        document.querySelectorAll('a[href]').forEach((a) => {
                            const href = a.href || '';
                            const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
                            const isMynavi = href.includes('mynavi.jp');
                            const isJob = href.includes('/jobinfo-') || href.includes('/job/')
                                || href.includes('corpinfo') || href.includes('/recruit/');
                            if (!isMynavi || !isJob) return;
                            if (!text || text.length < 4) return;
                            const clean = href.split('?')[0];
                            if (seen.has(clean)) return;
                            seen.add(clean);
                            results.push({ href: clean, title: text });
                        });
                        return results;
                    }"""
                )

                for item in links:
                    if item["href"] not in seen:
                        seen.add(item["href"])
                        all_links.append(item)
            except Exception as exc:
                logger.warning("Mynavi listing fetch failed for %s: %s", search_url, exc)

        if not all_links:
            await page.goto(MYNAVI_ENGINEER_HUB, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(self.delay)
            links = await page.evaluate(
                """() => {
                    const results = [];
                    const seen = new Set();
                    document.querySelectorAll('a[href]').forEach((a) => {
                        const href = a.href || '';
                        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
                        if (!href.includes('tenshoku.mynavi.jp')) return;
                        if (!href.includes('/jobinfo-')) return;
                        if (!text || seen.has(href)) return;
                        seen.add(href);
                        results.push({ href, title: text });
                    });
                    return results;
                }"""
            )
            all_links = links

        filtered = [l for l in all_links if self._is_relevant_job(l.get("title", ""))]
        if not filtered:
            filtered = [l for l in all_links if "エンジニア" in l.get("title", "")]

        return filtered[:max_results]

    async def _scrape_job_detail(self, page, href: str, fallback_title: str) -> Optional[ScrapedJob]:
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(self.delay * 0.5)

            page_text = await page.inner_text("body")
            title = await page.evaluate(
                """() => {
                    const h1 = document.querySelector('h1');
                    if (h1) return h1.innerText.trim();
                    const t = document.querySelector('.jobOfferTitle, .occName, .jobTitle');
                    return t ? t.innerText.trim() : '';
                }"""
            )
            company = await page.evaluate(
                """() => {
                    const el = document.querySelector(
                        '.companyName, .company, a[href*="corp"], .corpName'
                    );
                    return el ? el.innerText.trim() : '';
                }"""
            )

            job_title = title or fallback_title
            if not job_title:
                return None

            location_match = re.search(
                r"(東京都|大阪府|京都府|神奈川県|愛知県|福岡県|北海道|リモート|在宅|全国|日本)",
                page_text,
            )
            location = location_match.group(1) if location_match else "日本"

            requirements: list[str] = []
            for kw in FRESHMAN_KEYWORDS + TECH_KEYWORDS:
                if kw in page_text or kw.lower() in page_text.lower():
                    if kw not in requirements:
                        requirements.append(kw)

            return ScrapedJob(
                job_title=job_title,
                company=company or "Unknown",
                location=location,
                description=page_text[:3000],
                salary=self._parse_salary(page_text),
                requirements=requirements[:10],
                source_platform="mynavi",
                visa_sponsorship="ビザ" in page_text or "visa" in page_text.lower(),
                japanese_level=self._parse_japanese_level(page_text),
                remote_option="リモート" in page_text or "在宅" in page_text,
                job_url=href,
            )
        except Exception as exc:
            logger.warning("Mynavi detail scrape failed for %s: %s", href, exc)
            return None

    async def search_jobs(
        self,
        job_title: str = "",
        location: str = "",
        max_results: Optional[int] = None,
        **_kwargs,
    ) -> list[ScrapedJob]:
        """Scrape Mynavi entry-level and new-grad tech jobs."""
        logger.info("Mynavi scraping started")
        max_results = max_results or min(15, settings.scrape_max_jobs)
        results: list[ScrapedJob] = []

        keyword = job_title or "未経験 エンジニア"
        if job_title and "未経験" not in job_title and "新卒" not in job_title:
            keyword = f"{job_title} 未経験"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=USER_AGENT,
                locale="ja-JP",
            )
            page = await context.new_page()

            try:
                links = await self._collect_listing_links(page, keyword, max_results)
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

        logger.info("Mynavi jobs found: %d", len(results))
        return results


mynavi_scraper = MynaviScraper()
