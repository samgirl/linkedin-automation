"""
LinkedIn API Service — Handles real LinkedIn API integration.

LinkedIn API access:
- Marketing API: For companies/pages (requires partner approval)
- Sign In with LinkedIn: For basic profile
- Community Management API: For reading/commenting (limited access)

For V1, we support:
1. Manual post URL analysis (user pastes URL, we analyze via web scraping)
2. RSS feed monitoring (if available)
3. User-provided search terms → web search results
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.connector import Connection
from app.services.context_engine import ContextEngine
from app.services.llm import LLMOrchestrator
from app.utils.crypto import decrypt_token

logger = logging.getLogger(__name__)


class LinkedInAPIService:
    """Service for interacting with LinkedIn's API and web interface."""

    LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = LLMOrchestrator()

    async def get_user_profile(self, user_id: str) -> dict:
        """Get LinkedIn profile data for the user."""
        conn = await self._get_connection(user_id, "linkedin")
        if not conn or not conn.access_token_encrypted:
            return {"error": "LinkedIn not connected"}

        access_token = decrypt_token(conn.access_token_encrypted)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.LINKEDIN_API_BASE}/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.debug(f"LinkedIn profile fetch failed: {type(e).__name__}")
        return {"error": "Failed to fetch profile"}

    async def get_user_connections(self, user_id: str) -> list:
        """Get user's LinkedIn connections (requires appropriate scopes)."""
        conn = await self._get_connection(user_id, "linkedin")
        if not conn or not conn.access_token_encrypted:
            return []

        access_token = decrypt_token(conn.access_token_encrypted)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.LINKEDIN_API_BASE}/connections",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("elements", [])
        except Exception as e:
            logger.debug(f"LinkedIn connections fetch failed: {type(e).__name__}")
        return []

    async def analyze_post(self, post_url: str) -> dict:
        """Analyze a LinkedIn post from its URL.

        Uses web scraping + AI to extract insights.
        """
        content = await self._scrape_post(post_url)
        if not content:
            return {"error": "Could not fetch post content"}

        analysis_prompt = f"""Analyze this LinkedIn post:

{content}

Provide:
1. main_topic: What the post is about
2. key_points: Array of main arguments/points
3. sentiment: positive | negative | neutral | mixed
4. engagement_potential: high | medium | low
5. suggested_angle: A unique angle for responding
6. author_expertise: What the author seems expert in
7. relevant_hashtags: Array of relevant hashtags

Return as JSON."""

        analysis = await self.llm.generate(
            analysis_prompt,
            max_tokens=1000,
            response_format="json"
        )

        return analysis if isinstance(analysis, dict) else {"error": "Analysis failed"}

    async def _scrape_post(self, url: str) -> Optional[str]:
        """Scrape LinkedIn post content from URL."""
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                if resp.status_code == 200:
                    text = resp.text
                    # Try og:description meta tag
                    for marker in ['<meta property="og:description" content="']:
                        idx = text.find(marker)
                        if idx > -1:
                            start = idx + len(marker)
                            end = text.find('"', start)
                            if end > start:
                                return text[start:end]
                    # Fallback
                    return text[:3000]
        except Exception as e:
            logger.debug(f"LinkedIn post scrape failed: {type(e).__name__}")
        return None

    async def _get_connection(self, user_id: str, provider: str) -> Optional[Connection]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Connection).where(
                Connection.user_id == user_id,
                Connection.provider == provider,
                Connection.status == "active",
            )
        )
        return result.scalar_one_or_none()
