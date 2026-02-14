from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from urllib.parse import urlparse

from monitor.crawl.fetch import DomainRateLimiter, fetch_with_retries
from monitor.crawl.heuristics import HEURISTIC_PATHS, is_document_url, is_high_relevance
from monitor.crawl.html_extract import extract_links, html_looks_js_driven
from monitor.crawl.playwright_fetch import fetch_rendered_html
from monitor.crawl.sitemap import discover_sitemaps, parse_sitemap_urls

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    pages_fetched: int
    docs_found: list[dict]
    http_errors: int
    timeouts: int
    notes: list[str]


def crawl_jurisdiction(base_url: str, timeout: int, user_agent: str, playwright_enabled: bool = False) -> CrawlResult:
    limiter = DomainRateLimiter(max_per_second=2.0)

    seen: set[str] = set()
    q = deque()
    docs_found: list[dict] = []
    http_errors = 0
    timeouts = 0
    pages_fetched = 0
    notes: list[str] = []
    domain = urlparse(base_url).netloc

    for sitemap_url in discover_sitemaps(base_url, user_agent, timeout, limiter=limiter):
        try:
            sres = fetch_with_retries(sitemap_url, user_agent, timeout, limiter=limiter)
            if sres.status_code == 200:
                for u in parse_sitemap_urls(sres.content):
                    if urlparse(u).netloc == domain and is_high_relevance(u):
                        q.append((u, 0))
        except Exception:
            continue

    for p in HEURISTIC_PATHS:
        q.append((f"{base_url}{p}", 0))

    while q:
        url, depth = q.popleft()
        if url in seen or depth > 2:
            continue
        seen.add(url)
        try:
            res = fetch_with_retries(url, user_agent, timeout, limiter=limiter)
        except TimeoutError:
            timeouts += 1
            continue
        except Exception:
            http_errors += 1
            continue

        if res.status_code != 200:
            http_errors += 1
            continue

        ctype = res.headers.get("Content-Type", "").lower()
        if any(x in ctype for x in ["application/pdf", "application/msword", "application/vnd.openxmlformats"]):
            docs_found.append({"url": url, "title": "", "high_relevance": is_high_relevance(url)})
            continue

        pages_fetched += 1
        html = res.text
        links = extract_links(url, html)
        if not links and playwright_enabled and html_looks_js_driven(html):
            try:
                html = fetch_rendered_html(url)
                links = extract_links(url, html)
                notes.append("requires_js_rendering")
            except Exception:
                notes.append("js_rendering_failed")

        for link, title in links:
            if urlparse(link).netloc != domain:
                continue
            if is_document_url(link):
                docs_found.append({"url": link, "title": title, "high_relevance": is_high_relevance(link + " " + title)})
            elif depth < 2 and is_high_relevance(link + " " + title):
                q.append((link, depth + 1))

    return CrawlResult(pages_fetched, docs_found, http_errors, timeouts, notes)
