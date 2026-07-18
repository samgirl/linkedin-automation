"""Content generator - turns memories and opportunities into draft content."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from pros.src.ai.orchestrator import get_ai
from pros.src.db.models import Draft, Opportunity, Memory
from pros.src.utils import generate_id, utcnow


@dataclass
class ContentRequest:
    """Request for content generation."""
    
    content_type: str  # post, comment, article, thread
    topic: str
    context: Optional[str] = None
    tone: str = "professional"
    length: str = "medium"  # short, medium, long
    include_opportunities: bool = False


@dataclass
class GeneratedContent:
    """Generated content result."""
    
    content_type: str
    title: Optional[str]
    body: str
    topics: list[str]
    metadata: dict


class ContentGenerator:
    """Generates content from memories and opportunities."""
    
    def __init__(self, session):
        self.session = session
        self.ai = get_ai()
    
    async def generate(
        self,
        user_id: str,
        request: ContentRequest,
    ) -> GeneratedContent:
        """Generate content based on request."""
        
        # Gather context
        context_parts = []
        
        # Add user's recent memories
        memories = await self._get_recent_memories(user_id)
        if memories:
            memory_text = "\n".join([
                f"- {m.content[:200]}"
                for m in memories[:5]
            ])
            context_parts.append(f"Recent work:\n{memory_text}")
        
        # Add relevant opportunities if requested
        if request.include_opportunities:
            opportunities = await self._get_relevant_opportunities(
                user_id, request.topic
            )
            if opportunities:
                opp_text = "\n".join([
                    f"- {o.title}: {o.description[:150]}"
                    for o in opportunities[:3]
                ])
                context_parts.append(f"Relevant opportunities:\n{opp_text}")
        
        # Add explicit context
        if request.context:
            context_parts.append(f"Additional context:\n{request.context}")
        
        full_context = "\n\n".join(context_parts)
        
        # Generate content
        prompt = self._build_prompt(request, full_context)
        
        response = await self.ai.complete(
            prompt,
            temperature=0.7,
            max_tokens=self._get_max_tokens(request.length),
        )
        
        # Parse response
        return self._parse_response(response, request.content_type)
    
    async def generate_linkedin_post(
        self,
        user_id: str,
        topic: str,
        include_opportunities: bool = False,
    ) -> GeneratedContent:
        """Generate a LinkedIn post."""
        request = ContentRequest(
            content_type="post",
            topic=topic,
            include_opportunities=include_opportunities,
        )
        return await self.generate(user_id, request)
    
    async def generate_linkedin_comment(
        self,
        user_id: str,
        post_url: str,
        post_content: str,
    ) -> GeneratedContent:
        """Generate a LinkedIn comment."""
        request = ContentRequest(
            content_type="comment",
            topic="engagement",
            context=f"Post to comment on:\n{post_content}\nURL: {post_url}",
        )
        return await self.generate(user_id, request)
    
    async def generate_article(
        self,
        user_id: str,
        topic: str,
        outline: Optional[str] = None,
    ) -> GeneratedContent:
        """Generate a longer article."""
        request = ContentRequest(
            content_type="article",
            topic=topic,
            context=outline,
            length="long",
        )
        return await self.generate(user_id, request)
    
    async def generate_thread(
        self,
        user_id: str,
        topic: str,
        num_tweets: int = 5,
    ) -> GeneratedContent:
        """Generate a thread (Twitter/LinkedIn)."""
        request = ContentRequest(
            content_type="thread",
            topic=topic,
            length="long",
            context=f"Create a thread with {num_tweets} posts",
        )
        return await self.generate(user_id, request)
    
    def _build_prompt(self, request: ContentRequest, context: str) -> str:
        """Build generation prompt."""
        
        type_instructions = {
            "post": "Write a LinkedIn post",
            "comment": "Write a LinkedIn comment",
            "article": "Write a detailed article",
            "thread": "Write a thread",
        }
        
        length_instructions = {
            "short": "Keep it concise (100-200 words)",
            "medium": "Write a medium-length piece (300-500 words)",
            "long": "Write a comprehensive piece (800-1500 words)",
        }
        
        prompt = f"""{type_instructions.get(request.content_type, 'Write content')} about {request.topic}.

{length_instructions.get(request.length, '')}

Tone: {request.tone}
Style: First person, authentic, professional

Context from my work and experience:
{context}

Requirements:
1. Be specific and authentic - reference actual work and insights
2. Include actionable takeaways
3. End with a clear call-to-action or question
4. Use short paragraphs for readability
5. Include relevant emojis sparingly

Generate the content:"""
        
        return prompt
    
    def _get_max_tokens(self, length: str) -> int:
        """Get max tokens based on length."""
        return {
            "short": 300,
            "medium": 600,
            "long": 1500,
        }.get(length, 600)
    
    def _parse_response(
        self, response: str, content_type: str
    ) -> GeneratedContent:
        """Parse AI response into content."""
        # Extract title if present (first line if it looks like a title)
        lines = response.strip().split("\n")
        title = None
        body = response
        
        if lines and len(lines[0]) < 100 and not lines[0].endswith('.'):
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
        
        return GeneratedContent(
            content_type=content_type,
            title=title,
            body=body,
            topics=[],  # Could extract topics here
            metadata={"generated_at": utcnow().isoformat()},
        )
    
    async def _get_recent_memories(self, user_id: str) -> list:
        """Get recent memories for context."""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.created_at.desc())
            .limit(10)
        )
        return result.scalars().all()
    
    async def _get_relevant_opportunities(
        self, user_id: str, topic: str
    ) -> list:
        """Get relevant opportunities for context."""
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Opportunity)
            .where(Opportunity.user_id == user_id)
            .where(Opportunity.status == "pending")
            .order_by(Opportunity.created_at.desc())
            .limit(5)
        )
        return result.scalars().all()
