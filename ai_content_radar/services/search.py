"""Search system for discovering relevant discussions."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import unquote

import httpx

from ai_content_radar.config.settings import config
from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class SearchEngine:
    """Searches multiple sources for relevant discussions."""

    def __init__(self, db: DatabaseManager, taxonomy: KeywordTaxonomy):
        self.db = db
        self.taxonomy = taxonomy
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def search_linkedin(
        self,
        keywords: list[str],
        domains: Optional[list[str]] = None,
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        """Search for LinkedIn posts using Startpage as proxy."""
        results = []
        search_terms = keywords if keywords else self.taxonomy.get_search_terms(domains)

        for term in search_terms[:20]:
            try:
                posts = self._fetch_linkedin_via_startpage(term, max_per_query=max_results // max(len(search_terms[:20]), 1))
                results.extend(posts)
            except Exception as e:
                logger.error(f"Search failed for term '{term}': {e}")
                continue

        deduplicated = self._deduplicate(results)
        logger.info(f"LinkedIn search returned {len(deduplicated)} unique posts from {len(results)} total")
        return deduplicated[:max_results]

    def search_web(
        self,
        keywords: list[str],
        domains: Optional[list[str]] = None,
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        """Search the web using Startpage for relevant content."""
        results = []
        search_terms = keywords if keywords else self.taxonomy.get_search_terms(domains)

        for term in search_terms[:15]:
            try:
                posts = self._fetch_web_via_startpage(term, max_per_query=max_results // max(len(search_terms[:15]), 1))
                results.extend(posts)
            except Exception as e:
                logger.error(f"Web search failed for term '{term}': {e}")
                continue

        deduplicated = self._deduplicate(results)
        logger.info(f"Web search returned {len(deduplicated)} unique posts from {len(results)} total")
        return deduplicated[:max_results]

    def search_all(
        self,
        keywords: Optional[list[str]] = None,
        domains: Optional[list[str]] = None,
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        """Search all available sources."""
        all_results = []

        try:
            linkedin_results = self.search_linkedin(keywords or [], domains, max_results // 2)
            all_results.extend(linkedin_results)
        except Exception as e:
            logger.warning(f"LinkedIn search failed: {e}")

        try:
            web_results = self.search_web(keywords or [], domains, max_results // 2)
            all_results.extend(web_results)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

        deduplicated = self._deduplicate(all_results)
        return deduplicated[:max_results]

    def _fetch_linkedin_via_startpage(self, query: str, max_per_query: int = 20) -> list[dict[str, Any]]:
        """Fetch LinkedIn posts via Startpage search."""
        posts = []
        search_query = f"linkedin {query}"

        try:
            r = self.client.post(
                "https://www.startpage.com/sp/search",
                data={"query": search_query, "cat": "web", "language": "english"},
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 200:
                result_links = re.findall(
                    r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="([^"]+)"[^>]*>',
                    r.text,
                )
                titles_raw = re.findall(
                    r'class="[^"]*result-title[^"]*"[^>]*>(.*?)</(?:a|h2|div)',
                    r.text,
                    re.DOTALL,
                )
                title_idx = 0
                for link in result_links[:max_per_query]:
                    if "linkedin.com" in link:
                        title = ""
                        if title_idx < len(titles_raw):
                            title = re.sub(r'<[^>]+>', '', titles_raw[title_idx]).strip()
                            title_idx += 1
                        post_data = self._parse_linkedin_url(link, query)
                        if post_data:
                            if title:
                                post_data["title"] = title
                            posts.append(post_data)
        except Exception as e:
            logger.error(f"Startpage LinkedIn fetch error for '{query}': {e}")

        return posts

    def _fetch_web_via_startpage(self, query: str, max_per_query: int = 15) -> list[dict[str, Any]]:
        """Fetch web results using Startpage."""
        posts = []

        try:
            r = self.client.post(
                "https://www.startpage.com/sp/search",
                data={"query": query, "cat": "web", "language": "english"},
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 200:
                result_links = re.findall(
                    r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="([^"]+)"[^>]*>',
                    r.text,
                )
                titles_raw = re.findall(
                    r'class="[^"]*result-title[^"]*"[^>]*>(.*?)</(?:a|h2|div)',
                    r.text,
                    re.DOTALL,
                )

                for i, url in enumerate(result_links[:max_per_query]):
                    if not url.startswith("http"):
                        continue

                    title = ""
                    if i < len(titles_raw):
                        title = re.sub(r'<[^>]+>', '', titles_raw[i]).strip()

                    posts.append({
                        "url": url,
                        "title": title,
                        "text": title,
                        "author_name": "",
                        "author_title": "",
                        "organization": "",
                        "date_posted": None,
                        "engagement_likes": 0,
                        "engagement_comments": 0,
                        "engagement_shares": 0,
                        "hashtags": [],
                        "mentioned_companies": [],
                        "mentioned_orgs": [],
                        "mentioned_tech": [],
                        "source": "web",
                        "search_query": query,
                    })
        except Exception as e:
            logger.error(f"Startpage web fetch error for '{query}': {e}")

        return posts

    def _parse_linkedin_url(self, url: str, query: str) -> Optional[dict[str, Any]]:
        """Parse a LinkedIn post URL into structured data."""
        url = url.split("?")[0].rstrip("/")
        return {
            "url": url,
            "title": "",
            "text": f"LinkedIn post about: {query}",
            "author_name": "",
            "author_title": "",
            "organization": "",
            "date_posted": None,
            "engagement_likes": 0,
            "engagement_comments": 0,
            "engagement_shares": 0,
            "hashtags": [],
            "mentioned_companies": [],
            "mentioned_orgs": [],
            "mentioned_tech": [],
            "source": "linkedin",
            "search_query": query,
        }

    def store_results(self, results: list[dict[str, Any]]) -> tuple[int, int]:
        """Store search results in database. Returns (stored, duplicates)."""
        stored = 0
        duplicates = 0
        for post_data in results:
            result = self.db.add_post(post_data)
            if result:
                stored += 1
            else:
                duplicates += 1
        logger.info(f"Stored {stored} new posts, {duplicates} duplicates")
        return stored, duplicates

    def _deduplicate(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate results by URL."""
        seen_urls: set[str] = set()
        unique = []
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(r)
        return unique

    def get_cache_key(self, query: str, domains: list[str]) -> str:
        raw = f"{query}:{':'.join(sorted(domains))}"
        return f"search:{hashlib.md5(raw.encode()).hexdigest()}"

    def close(self) -> None:
        self.client.close()
