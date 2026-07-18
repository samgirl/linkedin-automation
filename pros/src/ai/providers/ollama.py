"""Ollama AI provider."""

import httpx

from pros.src.ai.providers.base import AIProvider


class OllamaProvider(AIProvider):
    """Ollama AI provider for local inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a completion using Ollama."""
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a chat completion using Ollama."""
        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("message", {}).get("content", "")
    
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding using Ollama."""
        response = await self.client.post(
            "/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("embedding", [])
