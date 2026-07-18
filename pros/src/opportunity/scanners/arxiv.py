"""ArXiv scanner - finds relevant research papers."""

import re
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

import httpx

from pros.src.opportunity.scanners.base import BaseScanner, ScanResult


# Default search queries
DEFAULT_QUERIES = [
    "technology transfer",
    "biotech manufacturing",
    "synthetic biology scale-up",
    "industrial automation",
    "precision fermentation",
    "cellular agriculture",
]


class ArxivScanner(BaseScanner):
    """Scans ArXiv for relevant research papers."""
    
    name = "arxiv"
    
    def __init__(self, queries: Optional[list[str]] = None):
        self.queries = queries or DEFAULT_QUERIES
        self.base_url = "http://export.arxiv.org/api/query"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def scan(self, user_id: str) -> list[ScanResult]:
        """Scan ArXiv for relevant papers."""
        results = []
        
        for query in self.queries:
            try:
                query_results = await self._search(query)
                results.extend(query_results)
            except Exception as e:
                print(f"ArXiv search failed for {query}: {e}")
                continue
        
        return results
    
    async def _search(self, query: str) -> list[ScanResult]:
        """Search ArXiv for a query."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 10,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        
        response = await self.client.get(self.base_url, params=params)
        
        if response.status_code != 200:
            return []
        
        return self._parse_response(response.text)
    
    def _parse_response(self, xml_content: str) -> list[ScanResult]:
        """Parse ArXiv API response."""
        results = []
        
        try:
            root = ElementTree.fromstring(xml_content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall("atom:entry", ns):
                title = self._get_text(entry, "atom:title", ns)
                summary = self._get_text(entry, "atom:summary", ns)
                published = self._get_text(entry, "atom:published", ns)
                
                # Get link
                link = None
                for link_el in entry.findall("atom:link", ns):
                    if link_el.get("type") == "text/html":
                        link = link_el.get("href")
                        break
                if not link:
                    id_el = entry.find("atom:id", ns)
                    if id_el is not None:
                        link = id_el.text
                
                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = self._get_text(author, "atom:name", ns)
                    if name:
                        authors.append(name)
                
                # Get categories
                categories = []
                for cat in entry.findall("atom:category", ns):
                    term = cat.get("term")
                    if term:
                        categories.append(term)
                
                if link:
                    results.append(ScanResult(
                        url=link,
                        title=self._clean_text(title or "Untitled"),
                        description=self._clean_text(summary or "")[:500],
                        source="arxiv",
                        author=", ".join(authors[:3]),
                        published_at=self._parse_date(published),
                        topics=categories,
                        metadata={
                            "authors": authors,
                            "categories": categories,
                        },
                    ))
        
        except ElementTree.ParseError as e:
            print(f"Failed to parse ArXiv response: {e}")
        
        return results
    
    def _get_text(self, element, tag: str, ns: dict) -> Optional[str]:
        """Get text content from an element."""
        el = element.find(tag, ns)
        return el.text if el is not None else None
    
    def _clean_text(self, text: str) -> str:
        """Clean whitespace from text."""
        return re.sub(r'\s+', ' ', text).strip()
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string."""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None
