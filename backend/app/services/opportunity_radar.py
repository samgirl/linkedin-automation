import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.user import User
from app.models.connector import Connection
from app.models.context import Memory, Identity
from app.services.context_engine import ContextEngine
from app.services.llm import LLMOrchestrator

ANALYSIS_PROMPT = """Analyze the following professional context data and extract identity traits.

Return a JSON array of identity traits. Each trait should have:
- type: one of "expertise", "interest", "communication_style", "goal", "value", "industry"
- name: short label for the trait
- data: object with "description" and "evidence" fields
- confidence: 0.0 to 1.0

Focus on:
1. What the person is an expert in
2. What topics they care about
3. How they communicate (formal, casual, technical, etc.)
4. What their professional goals seem to be
5. What values they express
6. What industry/industries they operate in

Data to analyze:
"""


class OpportunityRadar:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_engine = ContextEngine(db)
        self.llm = LLMOrchestrator()

    async def analyze_and_build_identity(self, user_id: str) -> list[dict]:
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.archived == False,
            ).order_by(desc(Memory.importance)).limit(100)
        )
        memories = result.scalars().all()
        if not memories:
            return []

        context_text = "\n".join(f"[{m.type}] {m.content}" for m in memories)
        analysis_text = ANALYSIS_PROMPT + context_text[:6000]

        try:
            response = await self.llm.complete(
                "You are a professional identity analyst. Return valid JSON only.",
                analysis_text,
            )
            traits = json.loads(response)
        except (json.JSONDecodeError, Exception):
            traits = [
                {
                    "type": "interest",
                    "name": "Professional Development",
                    "data": {"description": "Active in professional growth", "evidence": "Journal entries and content saved"},
                    "confidence": 0.5,
                }
            ]

        for trait in traits:
            existing = await self.db.execute(
                select(Identity).where(
                    Identity.user_id == user_id,
                    Identity.type == trait.get("type", ""),
                    Identity.name == trait.get("name", ""),
                )
            )
            node = existing.scalar_one_or_none()
            if node:
                node.confidence = max(node.confidence, trait.get("confidence", 0.5))
                node.data = trait.get("data", node.data)
            else:
                node = Identity(
                    user_id=user_id,
                    type=trait.get("type", "interest"),
                    name=trait.get("name", ""),
                    data=trait.get("data", {}),
                    confidence=trait.get("confidence", 0.5),
                )
                self.db.add(node)

        await self.db.flush()
        return traits

    async def find_opportunities(self, user_id: str) -> list[dict]:
        result = await self.db.execute(
            select(Identity).where(Identity.user_id == user_id)
        )
        identities = result.scalars().all()

        topics = [f"{n.name}: {n.data.get('description', '')}" for n in identities[:10]]

        if not topics:
            return []

        topic_text = ", ".join(topics)
        prompt = f"""Given these professional interests and expertise areas: {topic_text}

Suggest 5 LinkedIn engagement opportunities. For each, return a JSON array with objects containing:
- type: "post_idea", "comment", "connect", or "share"
- title: short title
- description: detailed description of the opportunity
- topics: array of relevant topic strings
- recommended_action: what specifically to do
- reasoning: why this is a good opportunity

Focus on genuine value-add opportunities, not engagement bait."""

        try:
            response = await self.llm.complete(
                "You are a LinkedIn strategy expert. Return valid JSON array only.",
                prompt,
            )
            opportunities = json.loads(response)
        except (json.JSONDecodeError, Exception):
            opportunities = [
                {
                    "type": "post_idea",
                    "title": "Share your expertise",
                    "description": "Write about something you worked on recently",
                    "topics": topics[:3],
                    "recommended_action": "Write a post about your recent work",
                    "reasoning": "Sharing real work builds authentic reputation",
                }
            ]

        from app.models.opportunity import Opportunity
        for opp_data in opportunities:
            opp = Opportunity(
                user_id=user_id,
                type=opp_data.get("type", "post_idea"),
                title=opp_data.get("title", ""),
                description=opp_data.get("description", ""),
                topics=opp_data.get("topics", []),
                scores={"relevance": 0.8, "timeliness": 0.7, "engagement": 0.7, "strategic": 0.8},
                recommended_action=opp_data.get("recommended_action", ""),
                reasoning=opp_data.get("reasoning", ""),
            )
            self.db.add(opp)

        await self.db.flush()
        return opportunities
