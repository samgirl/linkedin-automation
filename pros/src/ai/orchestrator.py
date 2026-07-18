"""AI orchestrator - routes requests to appropriate providers."""

from typing import Optional

from pros.src.config.settings import settings
from pros.src.ai.providers.ollama import OllamaProvider
from pros.src.ai.providers.base import AIProvider


class AIOrchestrator:
    """Orchestrates AI requests across providers."""
    
    def __init__(self):
        self.providers: dict[str, AIProvider] = {}
        self._init_providers()
    
    def _init_providers(self) -> None:
        """Initialize AI providers."""
        # Always initialize Ollama (default, free)
        self.providers["ollama"] = OllamaProvider(
            base_url=settings.ai.ollama_base_url,
            model=settings.ai.ollama_model,
        )
        
        # Initialize OpenAI if API key provided
        if settings.ai.openai_api_key:
            from pros.src.ai.providers.openai import OpenAIProvider
            self.providers["openai"] = OpenAIProvider(
                api_key=settings.ai.openai_api_key,
                model=settings.ai.openai_model,
            )
        
        # Initialize OpenRouter if API key provided
        if settings.ai.openrouter_api_key:
            from pros.src.ai.providers.openrouter import OpenRouterProvider
            self.providers["openrouter"] = OpenRouterProvider(
                api_key=settings.ai.openrouter_api_key,
                model=settings.ai.openrouter_model,
            )
    
    def get_provider(self, name: Optional[str] = None) -> AIProvider:
        """Get an AI provider by name."""
        provider_name = name or settings.ai.provider
        
        if provider_name not in self.providers:
            # Fallback to Ollama
            provider_name = "ollama"
        
        return self.providers[provider_name]
    
    async def complete(
        self,
        prompt: str,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a completion."""
        p = self.get_provider(provider)
        
        return await p.complete(
            prompt,
            temperature=temperature or settings.ai.temperature,
            max_tokens=max_tokens or settings.ai.max_tokens,
        )
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a chat completion."""
        p = self.get_provider(provider)
        
        return await p.chat(
            messages,
            temperature=temperature or settings.ai.temperature,
            max_tokens=max_tokens or settings.ai.max_tokens,
        )
    
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding."""
        p = self.get_provider("ollama")
        return await p.embed(text)


# Global AI instance
_ai: Optional[AIOrchestrator] = None


def get_ai() -> AIOrchestrator:
    """Get the AI orchestrator instance."""
    global _ai
    if _ai is None:
        _ai = AIOrchestrator()
    return _ai
