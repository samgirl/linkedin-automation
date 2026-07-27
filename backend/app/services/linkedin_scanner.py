"""
LinkedIn Post Scanner — Finds real posts in the user's space to engage with.

Two modes:
1. RSS/Feed mode: Pull from LinkedIn's public feed via RSS or search URLs
2. Manual curation: User pastes a post URL, AI analyzes it and generates a comment
3. AI mode: Uses the user's context to search for relevant trending posts via web search
"""
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.context import Memory
from app.services.llm import LLMOrchestrator
from app.services.context_engine import ContextEngine
from app.services.vector_store import VectorStore


class LinkedInScanner:
    """Scans LinkedIn for posts relevant to the user's expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = LLMOrchestrator()
        self.context_engine = ContextEngine(db)
        self.vector_store = VectorStore()

    async def analyze_post_url(self, user_id: str, post_url: str) -> dict:
        """Analyze a specific LinkedIn post URL — extract context and suggest comment."""
        if not self.llm.has_key:
            return {"error": "AI features require an API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."}

        user = await self.db.get(User, user_id)
        if not user:
            return {"error": "User not found"}

        # Fetch post content
        post_content = await self._fetch_post_content(post_url)
        if not post_content:
            return {"error": "Could not fetch post content"}

        # Get user's identity for context
        identity = await self.context_engine.get_identity_summary(user_id)
        top_memories = await self.vector_store.search(user_id, post_content, n_results=5)

        # Generate a comment suggestion
        comment_prompt = f"""You are helping a LinkedIn user write a thoughtful comment on a post.

The post says:
{post_content}

About this user: {identity}

Relevant context from their past: {top_memories}

Write a comment that:
1. Adds genuine value (insight, experience, data)
2. Is NOT generic ("great post!", "so true", etc.)
3. Is 2-4 sentences max
4. Shows expertise without being preachy
5. Invites further conversation"""

        comment = await self.llm.generate(comment_prompt, max_tokens=200)

        # Generate a post idea inspired by this
        post_idea_prompt = f"""Based on this LinkedIn post the user found interesting:

{post_content}

About the user: {identity}

Suggest 1 post idea (2-3 sentences) the user could write that responds to or expands on this topic from their own unique perspective."""

        post_idea = await self.llm.generate(post_idea_prompt, max_tokens=200)

        return {
            "url": post_url,
            "post_content": post_content,
            "suggested_comment": comment,
            "inspired_post_idea": post_idea,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def scan_for_opportunities(self, user_id: str, topic: str = None) -> list:
        interests = await self.context_engine.get_interests(user_id)
        search_topic = topic or interests.get("primary_topics", "your industry")

        if not self.llm.has_key:
            return [
                {"url": "", "author": "Suggested", "title": f"Search LinkedIn for '{search_topic}' posts", "description": f"Look for trending posts about {search_topic} and add your perspective", "difficulty": "easy"},
            ]

        user = await self.db.get(User, user_id)
        if not user:
            return []

        identity = await self.context_engine.get_identity_summary(user_id)

        # Use web search to find relevant LinkedIn posts
        search_prompt = f"""You are a LinkedIn engagement strategist. The user's expertise: {identity}

Find 5-8 specific LinkedIn posts (with URLs if possible) that are currently trending in these areas: {search_topic}

For each post, provide:
1. The URL or description of the post
2. The author's name and why they're relevant
3. Why the user should comment (how their expertise applies)
4. A difficulty level: easy/medium/hard (how controversial or complex the topic is)

Return as JSON array."""

        opportunities = await self.llm.generate(
            search_prompt,
            max_tokens=2000,
            response_format="json"
        )

        return opportunities if isinstance(opportunities, list) else []

    async def generate_opportunities(self, user_id: str) -> list:
        interests = await self.context_engine.get_interests(user_id)
        topics = interests.get("primary_topics", "your industry")

        if not self.llm.has_key:
            return [
                {"type": "post_idea", "title": f"Share a lesson from your work in {topics}", "description": "Write about a real challenge you solved this week. Specific stories with concrete outcomes get the most engagement.", "suggested_action": "Open LinkedIn and write a post about a real problem you solved", "priority": "high"},
                {"type": "comment_opportunity", "title": f"Engage with leaders in {topics}", "description": "Find 3 posts from people in your industry and leave thoughtful, specific comments.", "suggested_action": "Search LinkedIn for posts about your topics and comment on 3", "priority": "medium"},
                {"type": "post_idea", "title": "Share an unpopular opinion", "description": "What's a common practice in your field that you disagree with? Share a respectful but firm contrarian take.", "suggested_action": "Think of one thing everyone does wrong and write about it", "priority": "high"},
            ]

        identity = await self.context_engine.get_identity_summary(user_id)
        memories = await self.context_engine.get_recent_memories(user_id, limit=10)

        prompt = f"""You are a LinkedIn engagement strategist for this person:

{identity}

Recent thoughts and context: {memories}

Generate 5-7 engagement opportunities. For each, provide:
1. title: What to look for or engage with
2. type: post_idea | comment_opportunity | outreach | trend
3. description: Why this matters for the user specifically
4. suggested_action: What to do (write a post, find and comment, send a connection request)
5. priority: high | medium | low

Focus on opportunities that align with their expertise and where they can genuinely add value.
Return as JSON array."""

        opportunities = await self.llm.generate(
            prompt,
            max_tokens=3000,
            response_format="json"
        )

        return opportunities if isinstance(opportunities, list) else []

    async def _fetch_post_content(self, url: str) -> Optional[str]:
        """Fetch LinkedIn post content from URL.

        Note: LinkedIn blocks most scraping. For V1, we use web search
        to get the post's cached/indexed content.
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try to get the page content
                resp = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    # Extract text from HTML (basic)
                    text = resp.text
                    # Try to find post content in meta tags or body
                    for marker in ['<meta property="og:description" content="', '<p class="share-']:
                        idx = text.find(marker)
                        if idx > -1:
                            start = text.find('"', idx + len(marker)) + 1
                            end = text.find('"', start)
                            if end > start:
                                return text[start:end]
                    # Fallback: return first 2000 chars of text
                    return text[:2000]
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"LinkedIn post fetch failed: {type(e).__name__}")
        return None
