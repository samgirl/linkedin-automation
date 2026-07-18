"""Base scanner interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ScanResult:
    """Result from a scanner."""
    
    url: str
    title: str
    description: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    topics: list[str] = field(default_factory=list)
    engagement: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class BaseScanner(ABC):
    """Base class for all scanners."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner name."""
        pass
    
    @abstractmethod
    async def scan(self, user_id: str) -> list[ScanResult]:
        """Scan for opportunities."""
        pass
