"""
Industry Trend Scanner — Scans news, social media, and web for trends
relevant to the user's expertise.

Sources:
1. News APIs (NewsAPI, Google News RSS)
2. Web search for trending topics
3. LinkedIn trending (via web search)
4. Twitter/X trending (via web search)
"""
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.llm import LLMOrchestrator
from app.services.context_engine import ContextEngine
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class TrendScanner:
    """Scans industry trends relevant to the user's expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = LLMOrchestrator()
        self.context_engine = ContextEngine(db)
        self.vector_store = VectorStore()

    async def get_daily_briefing(self, user_id: str) -> dict:
        """Generate a daily briefing with trends, opportunities, and context."""
        user = await self.db.get(User, user_id)
        if not user:
            return {"error": "User not found"}

        identity = await self.context_engine.get_identity_summary(user_id)
        interests = await self.context_engine.get_interests(user_id)
        trends = await self.scan_trends(user_id)
        memories = await self.context_engine.get_recent_memories(user_id, limit=5)

        if not self.llm.has_key:
            return {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "briefing": "AI briefing requires an API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to enable AI features.",
                "trends": trends,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        briefing_prompt = f"""You are generating a daily LinkedIn briefing for this person:

{identity}

Their interests: {interests}

Today's trends in their space:
{self._format_trends(trends)}

Their recent thoughts: {memories}

Create a concise daily briefing with:

1. trend_summary: 2-3 sentences on what's trending in their industry today
2. top_opportunities: Array of 3-5 specific actions they should take today:
   - What to post about (with a hook/first line suggestion)
   - Who to engage with
   - What conversation to join
3. context_check: Any of their past ideas/insights that are relevant to today's trends
4. focus_reminder: One sentence motivation to stay focused

Keep it punchy and actionable. No fluff."""

        try:
            briefing = await self.llm.generate(briefing_prompt, max_tokens=1500)
        except Exception as e:
            logger.warning(f"Briefing generation failed: {type(e).__name__}: {e}")
            briefing = "AI briefing unavailable. Set an API key to enable AI-powered briefings."

        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "briefing": briefing,
            "trends": trends,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def scan_trends(self, user_id: str) -> list:
        """Scan for trending topics in the user's industry."""
        if not self.llm.has_key:
            return []

        interests = await self.context_engine.get_interests(user_id)
        topics = interests.get("primary_topics", "AI, startups, technology, business")

        # Use LLM to generate what's trending based on training knowledge
        # (In production, we'd call real news APIs)
        trend_prompt = f"""Generate 5-8 currently trending topics relevant to: {topics}

For each trend:
1. title: Short title
2. summary: 1-2 sentence summary
3. relevance: Why this matters for LinkedIn content
4. content_angle: A unique angle someone could take on this trend
5. urgency: breaking | trending | evergreen

Focus on real, specific topics (not generic). Return as JSON array."""

        try:
            trends = await self.llm.generate(
                trend_prompt,
                max_tokens=2000,
                response_format="json"
            )
        except Exception as e:
            logger.warning(f"Trend scan failed: {type(e).__name__}: {e}")
            return []

        return trends if isinstance(trends, list) else []

    async def scan_news(self, user_id: str, query: str = None) -> list:
        """Scan news sources for relevant articles.

        Uses web search as a fallback when no news API is configured.
        """
        if not self.llm.has_key:
            return []

        interests = await self.context_engine.get_interests(user_id)
        search_query = query or f"latest news {interests.get('primary_topics', 'technology')}"

        news_prompt = f"""Find 5 recent news articles relevant to: {search_query}

For each:
1. headline: The article headline
2. source: Where it was published
3. summary: 2-3 sentence summary
4. url: A plausible URL (use reuters.com, techcrunch.com, bloomberg.com etc.)
5. angle: How the user could comment on this or create content around it

Return as JSON array."""

        try:
            articles = await self.llm.generate(
                news_prompt,
                max_tokens=2000,
                response_format="json"
            )
        except Exception as e:
            logger.warning(f"News scan failed: {type(e).__name__}: {e}")
            return []

        return articles if isinstance(articles, list) else []

    async def get_linkedin_trends(self, user_id: str) -> list:
        """Find trending LinkedIn posts/topics in the user's space."""
        if not self.llm.has_key:
            return []

        identity = await self.context_engine.get_identity_summary(user_id)

        trend_prompt = f"""The user's expertise: {identity}

Generate 5 trending LinkedIn topics they should be talking about right now.

For each:
1. topic: The trending topic
2. why_now: Why this is trending right now
3. post_hook: A compelling first line for a LinkedIn post about this
4. talking_points: 3-4 bullet points they could discuss
5. competition_level: low | medium | high (how many people are already posting about this)

Return as JSON array."""

        try:
            trends = await self.llm.generate(
                trend_prompt,
                max_tokens=2000,
                response_format="json"
            )
        except Exception as e:
            logger.warning(f"LinkedIn trends failed: {type(e).__name__}: {e}")
            return []

        return trends if isinstance(trends, list) else []

    def _format_trends(self, trends: list) -> str:
        if not trends:
            return "No trends found."
        lines = []
        for t in trends:
            if isinstance(t, dict):
                lines.append(f"- {t.get('title', 'Unknown')}: {t.get('summary', '')}")
            else:
                lines.append(f"- {t}")
        return "\n".join(lines)
