"""RSS scanner - monitors RSS/Atom feeds."""

import re
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

import httpx

from pros.src.opportunity.scanners.base import BaseScanner, ScanResult


# Default feeds to monitor
DEFAULT_FEEDS = [
    # Tech
    "https://news.ycombinator.com/rss",
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/startups/.rss",
    
    # Biotech
    "https://www.reddit.com/r/biotech/.rss",
    "https://www.reddit.com/r/syntheticbiology/.rss",
    
    # Manufacturing
    "https://www.reddit.com/r/manufacturing/.rss",
    
    # AI
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/LocalLLaMA/.rss",
]


class RSSScanner(BaseScanner):
    """Scans RSS/Atom feeds for relevant content."""
    
    name = "rss"
    
    def __init__(self, feeds: Optional[list[str]] = None):
        self.feeds = feeds or DEFAULT_FEEDS
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def scan(self, user_id: str) -> list[ScanResult]:
        """Scan all configured feeds."""
        results = []
        
        for feed_url in self.feeds:
            try:
                feed_results = await self._parse_feed(feed_url)
                results.extend(feed_results)
            except Exception as e:
                print(f"RSS scan failed for {feed_url}: {e}")
                continue
        
        return results
    
    async def _parse_feed(self, url: str) -> list[ScanResult]:
        """Parse an RSS/Atom feed."""
        response = await self.client.get(url)
        
        if response.status_code != 200:
            return []
        
        content = response.text
        results = []
        
        # Try RSS 2.0 format
        try:
            root = ElementTree.fromstring(content)
            
            # Handle RSS 2.0
            for item in root.findall(".//item"):
                title = self._get_text(item, "title")
                link = self._get_text(item, "link")
                description = self._get_text(item, "description")
                pub_date = self._get_text(item, "pubDate")
                
                if link:
                    results.append(ScanResult(
                        url=link,
                        title=title or "Untitled",
                        description=self._clean_html(description or ""),
                        source="rss",
                        published_at=self._parse_date(pub_date),
                        metadata={"feed_url": url},
                    ))
            
            # Handle Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                title = self._get_text(entry, "atom:title", ns)
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href") if link_el is not None else None
                summary = self._get_text(entry, "atom:summary", ns)
                published = self._get_text(entry, "atom:published", ns)
                
                if link:
                    results.append(ScanResult(
                        url=link,
                        title=title or "Untitled",
                        description=self._clean_html(summary or ""),
                        source="rss",
                        published_at=self._parse_date(published),
                        metadata={"feed_url": url},
                    ))
        
        except ElementTree.ParseError:
            pass
        
        return results
    
    def _get_text(self, element, tag: str, ns: Optional[dict] = None) -> Optional[str]:
        """Get text content from an element."""
        if ns:
            el = element.find(tag, ns)
        else:
            el = element.find(tag)
        
        return el.text if el is not None else None
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string."""
        if not date_str:
            return None
        
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
