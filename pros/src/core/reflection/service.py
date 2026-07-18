"""Reflection service - daily intelligent conversation."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.core.memory.service import MemoryService
from pros.src.core.identity.service import IdentityService
from pros.src.core.identity.models import NodeType
from pros.src.ai.orchestrator import get_ai
from pros.src.utils import utcnow


class ReflectionService:
    """Reflection service for daily intelligent conversations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_service = MemoryService(session)
        self.identity_service = IdentityService(session)
    
    async def generate_questions(self, user_id: str) -> list[dict]:
        """Generate intelligent questions based on context."""
        ai = get_ai()
        
        # Gather context
        identity = await self.identity_service.get_identity(user_id)
        recent_memories = await self.memory_service.list(
            user_id,
            limit=10,
            min_importance=0.3,
        )
        
        # Build context for question generation
        context_parts = []
        
        if identity.projects:
            projects = ", ".join([p.name for p in identity.projects[:5]])
            context_parts.append(f"Active projects: {projects}")
        
        if identity.goals:
            goals = ", ".join([g.name for g in identity.goals[:3]])
            context_parts.append(f"Current goals: {goals}")
        
        if recent_memories:
            recent = "\n".join([f"- {m.content[:100]}" for m in recent_memories[:5]])
            context_parts.append(f"Recent activities:\n{recent}")
        
        context = "\n".join(context_parts) if context_parts else "No specific context available."
        
        prompt = f"""Based on this professional context, generate 5 intelligent questions to understand their work better.

Context:
{context}

Generate questions that:
1. Are specific to their projects and work
2. Help uncover new insights or learning
3. Check on progress of ongoing work
4. Explore recent decisions or changes
5. Surface frustrations or challenges

Questions should feel like a thoughtful coworker asking, not an interrogation.

Return ONLY a JSON array of objects with "question" and "category" fields.
Example: [{{"question": "How did the API redesign go today?", "category": "project_progress"}}]"""

        response = await ai.complete(prompt, temperature=0.7, max_tokens=800)
        
        # Parse response
        try:
            import json
            questions = json.loads(response)
            return questions if isinstance(questions, list) else []
        except Exception:
            return [
                {"question": "What did you work on today?", "category": "daily_work"},
                {"question": "Any wins or breakthroughs?", "category": "achievements"},
                {"question": "What challenged you today?", "category": "challenges"},
                {"question": "Did you learn anything new?", "category": "learning"},
                {"question": "Any ideas or insights worth capturing?", "category": "ideas"},
            ]
    
    async def process_reflection(
        self,
        user_id: str,
        responses: list[dict],
    ) -> list[dict]:
        """Process reflection responses and extract memories."""
        ai = get_ai()
        extracted = []
        
        for response in responses:
            question = response.get("question", "")
            answer = response.get("answer", "")
            
            if not answer.strip():
                continue
            
            # Use AI to extract insights
            prompt = f"""Analyze this reflection response and extract key professional insights.

Question: {question}
Answer: {answer}

Extract:
1. What happened (event)
2. What was learned (learning)
3. Any achievements or wins
4. Any challenges or frustrations
5. Key topics or themes
6. People mentioned

Return a JSON object with:
- "memories": array of {{type, content, importance (0-1)}}
- "topics": array of topic strings
- "people": array of people mentioned

Types: meeting, learning, achievement, frustration, idea, project_update"""

            response_text = await ai.complete(prompt, temperature=0.5, max_tokens=500)
            
            try:
                import json
                insights = json.loads(response_text)
                
                # Create memories from insights
                for mem in insights.get("memories", []):
                    memory_type = mem.get("type", "episodic")
                    if memory_type not in ["episodic", "semantic", "belief", "pattern"]:
                        memory_type = "episodic"
                    
                    await self.memory_service.create(
                        user_id,
                        {
                            "type": memory_type,
                            "content": mem["content"],
                            "importance": mem.get("importance", 0.5),
                            "source": "reflection",
                            "tags": insights.get("topics", []),
                        }
                    )
                
                extracted.append({
                    "question": question,
                    "answer": answer,
                    "insights": insights,
                })
                
            except Exception:
                # Fallback: create basic memory
                await self.memory_service.create(
                    user_id,
                    {
                        "type": "episodic",
                        "content": f"Reflection: {question} -> {answer[:200]}",
                        "importance": 0.4,
                        "source": "reflection",
                    }
                )
        
        return extracted
    
    async def get_daily_summary(self, user_id: str, date: Optional[datetime] = None) -> str:
        """Generate a daily summary."""
        ai = get_ai()
        
        if date is None:
            date = utcnow()
        
        # Get today's memories
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        memories = await self.memory_service.list(user_id, limit=50)
        
        if not memories:
            return "No significant activities recorded today."
        
        # Generate summary
        memories_text = "\n".join([
            f"- [{m.type.value}] {m.content[:150]}"
            for m in memories[:20]
        ])
        
        prompt = f"""Generate a concise daily summary for this professional.

Today's activities:
{memories_text}

Create a brief summary that:
1. Highlights key achievements
2. Notes any learning or insights
3. Mentions challenges or blockers
4. Suggests focus for tomorrow

Keep it under 200 words. Write in a supportive, coworker tone."""

        return await ai.complete(prompt, temperature=0.7, max_tokens=300)
