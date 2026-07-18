"""Scanners module."""

from pros.src.opportunity.scanners.base import BaseScanner, ScanResult
from pros.src.opportunity.scanners.linkedin import LinkedInScanner
from pros.src.opportunity.scanners.github import GitHubScanner
from pros.src.opportunity.scanners.rss import RSSScanner
from pros.src.opportunity.scanners.arxiv import ArxivScanner

__all__ = [
    "BaseScanner",
    "ScanResult",
    "LinkedInScanner",
    "GitHubScanner",
    "RSSScanner",
    "ArxivScanner",
]
