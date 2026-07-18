"""Base AI provider interface."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers."""
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a completion."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a chat completion."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding."""
        pass
