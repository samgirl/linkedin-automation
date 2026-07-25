import httpx
from app.utils.crypto import decrypt_token
from app.services.context_engine import ContextEngine


class LinkedInConnector:
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token_encrypted: str):
        self.access_token = decrypt_token(access_token_encrypted)

    async def get_profile(self) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/userinfo",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            if resp.status_code == 200:
                return resp.json()
            return {}

    async def get_posts(self, limit: int = 20) -> list[dict]:
        profile = await self.get_profile()
        sub = profile.get("sub", "")
        if not sub:
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/ugcPosts",
                params={"q": "authors", "authors": f"List(urn:li:person:{sub})", "count": limit},
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("elements", [])
            return []

    async def get_feed(self, limit: int = 20) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/socialActions/feedPosts",
                params={"count": limit},
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("elements", [])
            return []

    async def sync_to_context(self, user_id: str, db) -> int:
        from app.models.connector import Connection
        from sqlalchemy import select

        engine = ContextEngine(db)
        count = 0

        profile = await self.get_profile()
        if profile:
            await engine.ingest_event(
                user_id=user_id,
                event_type="linkedin_profile",
                source="linkedin",
                title="LinkedIn Profile",
                content=f"Name: {profile.get('name', '')}, Headline: {profile.get('headline', '')}",
                metadata=profile,
            )
            count += 1

        posts = await self.get_posts()
        for post in posts:
            await engine.ingest_event(
                user_id=user_id,
                event_type="linkedin_post",
                source="linkedin",
                title="LinkedIn Post",
                content=post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", ""),
                metadata=post,
            )
            count += 1

        return count
