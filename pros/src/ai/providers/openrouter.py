"""OpenRouter provider."""

import httpx

from pros.src.ai.providers.base import AIProvider


class OpenRouterProvider(AIProvider):
    """OpenRouter API provider."""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://pros.dev",
                "X-Title": "PROS",
            },
            timeout=60.0,
        )
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a completion."""
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a chat completion."""
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding (uses Ollama as fallback for embeddings)."""
        # OpenRouter doesn't provide embeddings, fall back to local
        from pros.src.ai.providers.ollama import OllamaProvider
        ollama = OllamaProvider()
        return await ollama.embed(text)
