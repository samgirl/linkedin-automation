import json
import httpx
from app.config import get_settings

settings = get_settings()


class LLMOrchestrator:
    def __init__(self, api_key: str = None, provider: str = None):
        self.api_key = api_key or settings.anthropic_api_key or settings.openai_api_key
        self.provider = provider or settings.default_ai_provider

    async def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        if self.provider == "anthropic":
            return await self._anthropic_complete(system_prompt, user_prompt, max_tokens)
        elif self.provider == "openai":
            return await self._openai_complete(system_prompt, user_prompt, max_tokens)
        else:
            return await self._anthropic_complete(system_prompt, user_prompt, max_tokens)

    async def generate(self, prompt: str, max_tokens: int = 2000, response_format: str = None) -> any:
        """Simplified generate method used by scanner services."""
        system = "You are a helpful AI assistant. Always return valid JSON when requested."
        if response_format == "json":
            system += " Return your response as a valid JSON array or object. No markdown, no code fences, just raw JSON."

        text = await self.complete(system, prompt, max_tokens)

        if response_format == "json":
            return self._parse_json(text)
        return text

    def _parse_json(self, text: str) -> any:
        """Extract JSON from LLM response, handling common edge cases."""
        text = text.strip()
        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON array or object in the text
            for start_char, end_char in [("[", "]"), ("{", "}")]:
                start = text.find(start_char)
                end = text.rfind(end_char)
                if start != -1 and end > start:
                    try:
                        return json.loads(text[start:end + 1])
                    except json.JSONDecodeError:
                        continue
            return text

    async def _anthropic_complete(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            if resp.status_code != 200:
                raise Exception(f"LLM error: {resp.status_code} {resp.text}")
            data = resp.json()
            return data["content"][0]["text"]

    async def _openai_complete(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max_tokens,
                },
            )
            if resp.status_code != 200:
                raise Exception(f"LLM error: {resp.status_code} {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]
