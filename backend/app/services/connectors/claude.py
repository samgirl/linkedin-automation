import httpx
from app.utils.crypto import decrypt_token
from app.services.context_engine import ContextEngine


class ClaudeConnector:
    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key_encrypted: str):
        self.api_key = decrypt_token(api_key_encrypted)

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/models",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return []

    async def sync_to_context(self, user_id: str, db) -> int:
        engine = ContextEngine(db)
        count = 0

        models = await self.list_models()
        if models:
            await engine.ingest_event(
                user_id=user_id,
                event_type="claude_models",
                source="claude",
                title="Claude Models Available",
                content=f"Available models: {', '.join(m.get('id', '') for m in models[:10])}",
                metadata={"model_count": len(models)},
            )
            count += 1

        return count
