import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.opportunity import Opportunity, Draft
from app.services.context_engine import ContextEngine
from app.services.llm import LLMOrchestrator

logger = logging.getLogger(__name__)


POST_SYSTEM_PROMPT = """You are a LinkedIn content strategist. Generate LinkedIn posts based on the user's context.

Rules:
- Write in first person
- Be authentic, not corporate
- Use short paragraphs and line breaks for readability
- Include a hook in the first line
- End with a question or call-to-action
- No hashtags in the body (add 3-5 relevant hashtags at the end)
- Keep it under 300 words
- Match the user's communication style from their context
"""

COMMENT_SYSTEM_PROMPT = """You are a LinkedIn engagement expert. Generate thoughtful comments on posts.

Rules:
- Be genuine and add value
- Share a relevant experience or insight
- Ask a thoughtful follow-up question
- Keep it under 150 words
- Don't be generic — reference something specific from the post
"""

BRIEFING_SYSTEM_PROMPT = """You are a personal AI assistant. Generate a daily briefing for the user based on their context.

Format:
1. What you know about what the user worked on recently
2. Suggested focus areas for today
3. Any pending opportunities that need attention
4. A motivational note based on their recent work
"""

MESSAGE_SYSTEM_PROMPT = """You are a professional networking expert. Generate personalized connection messages.

Rules:
- Be specific about why you want to connect
- Reference shared interests or recent work
- Keep it under 50 words
- Be genuine, not salesy
"""


class ContentGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_engine = ContextEngine(db)
        self.llm = LLMOrchestrator()

    async def generate_for_opportunity(self, user_id: str, opportunity: Opportunity) -> Draft:
        if not self.llm.has_key:
            raise ValueError("AI features require an API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

        context = await self.context_engine.get_user_context_for_generation(user_id)

        if opportunity.type == "comment":
            system = COMMENT_SYSTEM_PROMPT
            user_prompt = f"Post to comment on:\nTitle: {opportunity.title}\nContent: {opportunity.description}\n\nMy context:\n{json.dumps(context, indent=2)[:3000]}"
        elif opportunity.type == "connect":
            system = MESSAGE_SYSTEM_PROMPT
            user_prompt = f"Person to connect with: {opportunity.title}\nAbout them: {opportunity.description}\n\nMy context:\n{json.dumps(context, indent=2)[:3000]}"
        else:
            system = POST_SYSTEM_PROMPT
            user_prompt = f"Topic: {opportunity.title}\nDetails: {opportunity.description}\n\nMy context:\n{json.dumps(context, indent=2)[:3000]}"

        content = await self.llm.complete(system, user_prompt)

        draft = Draft(
            user_id=user_id,
            opportunity_id=opportunity.id,
            type=opportunity.type,
            title=opportunity.title,
            content=content,
            platform="linkedin",
        )
        self.db.add(draft)
        await self.db.flush()
        return draft

    async def generate_standalone(self, user_id: str, draft_type: str, topic: str, extra_context: str = "") -> Draft:
        if not self.llm.has_key:
            raise ValueError("AI features require an API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

        context = await self.context_engine.get_user_context_for_generation(user_id)

        if draft_type == "comment":
            system = COMMENT_SYSTEM_PROMPT
        elif draft_type == "message":
            system = MESSAGE_SYSTEM_PROMPT
        else:
            system = POST_SYSTEM_PROMPT

        user_prompt = f"Topic: {topic}\nExtra context: {extra_context}\n\nMy context:\n{json.dumps(context, indent=2)[:3000]}"
        content = await self.llm.complete(system, user_prompt)

        draft = Draft(
            user_id=user_id,
            type=draft_type,
            title=topic,
            content=content,
            platform="linkedin",
        )
        self.db.add(draft)
        await self.db.flush()
        return draft

    async def generate_briefing(self, user_id: str) -> dict:
        context = await self.context_engine.get_user_context_for_generation(user_id)
        interests = await self.context_engine.get_interests(user_id)
        memory_count = len(context.get("memories", []))
        identity_count = len(context.get("identity", []))

        if not self.llm.has_key:
            topics = interests.get("primary_topics", "")
            tips = [
                "Share a lesson you learned this week — authenticity drives engagement.",
                "Comment on 3 posts in your industry before posting your own.",
                "Write about a problem you solved recently — specific stories perform best.",
                "Tag someone who inspired you this week and explain why.",
                "Share a hot take on a trending topic in your industry.",
            ]
            tip = tips[hash(user_id) % len(tips)]

            if memory_count == 0:
                progress = "You're just getting started! Add some journal entries about your work to unlock personalized insights."
            elif memory_count < 5:
                progress = f"Great start! You have {memory_count} memories stored. Keep adding journal entries to build your profile."
            else:
                progress = f"Your profile has {memory_count} memories and {identity_count} identity traits. You're building real momentum!"

            text = f"**Your Progress:** {progress}\n\n"
            if topics:
                text += f"**Your Focus Areas:** {topics}\n\n"
            text += f"**Today's Tip:** {tip}\n\n"
            text += "**Quick Actions:**\n"
            text += "- Add a journal entry about something you worked on\n"
            text += "- Generate opportunities to see what to post about\n"
            text += "- Check the Scanner for trending topics"
            return {"text": text, "memories_count": memory_count, "identity_count": identity_count}

        user_prompt = f"My recent context:\n{json.dumps(context, indent=2)[:4000]}"

        try:
            briefing_text = await self.llm.complete(BRIEFING_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"Briefing generation failed: {type(e).__name__}: {e}")
            briefing_text = "Add more context about your work to get personalized briefings."

        return {
            "text": briefing_text,
            "memories_count": memory_count,
            "identity_count": identity_count,
        }
