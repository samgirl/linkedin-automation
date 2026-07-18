"""Daily briefing generator - prepares morning summary."""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from pros.src.ai.orchestrator import get_ai
from pros.src.db.models import Opportunity, Memory, Draft, DailySummary
from pros.src.utils import generate_id, utcnow
from sqlalchemy import select


@dataclass
class Briefing:
    """Daily briefing content."""
    
    date: str
    summary: str
    priorities: list[str]
    opportunities: list[dict]
    suggested_actions: list[dict]
    reflection_question: str
    metrics: dict


class DailyBriefingGenerator:
    """Generates daily briefing for the morning."""
    
    def __init__(self, session):
        self.session = session
        self.ai = get_ai()
    
    async def generate(self, user_id: str) -> Briefing:
        """Generate daily briefing."""
        
        # Gather data
        opportunities = await self._get_pending_opportunities(user_id)
        recent_memories = await self._get_recent_memories(user_id)
        pending_drafts = await self._get_pending_drafts(user_id)
        
        # Generate summary
        summary = await self._generate_summary(
            opportunities, recent_memories, pending_drafts
        )
        
        # Generate priorities
        priorities = await self._generate_priorities(
            opportunities, recent_memories
        )
        
        # Generate suggested actions
        actions = await self._generate_actions(
            opportunities, pending_drafts
        )
        
        # Generate reflection question
        reflection = await self._generate_reflection(recent_memories)
        
        # Calculate metrics
        metrics = await self._calculate_metrics(user_id)
        
        briefing = Briefing(
            date=utcnow().strftime("%Y-%m-%d"),
            summary=summary,
            priorities=priorities,
            opportunities=[
                {
                    "title": o.title,
                    "description": o.description[:200],
                    "source": o.source,
                    "score": o.scores.get("relevance", 0) if o.scores else 0,
                }
                for o in opportunities[:5]
            ],
            suggested_actions=actions,
            reflection_question=reflection,
            metrics=metrics,
        )
        
        # Save to database
        await self._save_briefing(user_id, briefing)
        
        return briefing
    
    async def _get_pending_opportunities(self, user_id: str) -> list:
        """Get pending opportunities."""
        result = await self.session.execute(
            select(Opportunity)
            .where(Opportunity.user_id == user_id)
            .where(Opportunity.status == "pending")
            .order_by(Opportunity.created_at.desc())
            .limit(20)
        )
        return result.scalars().all()
    
    async def _get_recent_memories(self, user_id: str) -> list:
        """Get recent memories."""
        result = await self.session.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.created_at.desc())
            .limit(10)
        )
        return result.scalars().all()
    
    async def _get_pending_drafts(self, user_id: str) -> list:
        """Get pending drafts."""
        result = await self.session.execute(
            select(Draft)
            .where(Draft.user_id == user_id)
            .where(Draft.status == "pending")
            .order_by(Draft.created_at.desc())
            .limit(5)
        )
        return result.scalars().all()
    
    async def _generate_summary(
        self, opportunities, memories, drafts
    ) -> str:
        """Generate briefing summary."""
        opp_text = "\n".join([
            f"- {o.title}: {o.description[:100]}"
            for o in opportunities[:5]
        ]) or "No new opportunities"
        
        memory_text = "\n".join([
            f"- {m.content[:100]}"
            for m in memories[:3]
        ]) or "No recent work logged"
        
        prompt = f"""Generate a concise morning briefing summary.

New opportunities:
{opp_text}

Recent work:
{memory_text}

Pending drafts: {len(drafts)}

Write a 2-3 sentence summary of what to focus on today. Be specific and actionable."""
        
        return await self.ai.complete(prompt, temperature=0.5, max_tokens=200)
    
    async def _generate_priorities(
        self, opportunities, memories
    ) -> list[str]:
        """Generate today's priorities."""
        opp_text = "\n".join([
            f"- {o.title} ({o.source})"
            for o in opportunities[:5]
        ]) or "No opportunities"
        
        prompt = f"""Based on these opportunities, suggest 3 priorities for today:

{opp_text}

Return as a numbered list of short, actionable priorities."""
        
        response = await self.ai.complete(prompt, temperature=0.5, max_tokens=200)
        
        # Parse numbered list
        priorities = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove number and period
                priority = line.split(".", 1)[-1].strip()
                priorities.append(priority)
        
        return priorities[:3]
    
    async def _generate_actions(
        self, opportunities, drafts
    ) -> list[dict]:
        """Generate suggested actions."""
        actions = []
        
        # Actions from opportunities
        for opp in opportunities[:3]:
            action = await self._suggest_action_for_opportunity(opp)
            actions.append(action)
        
        # Actions from drafts
        for draft in drafts[:2]:
            actions.append({
                "type": "publish",
                "title": f"Review and publish: {draft.title or 'Untitled draft'}",
                "description": "Review your draft and publish when ready",
                "priority": "medium",
            })
        
        return actions
    
    async def _suggest_action_for_opportunity(self, opportunity) -> dict:
        """Suggest action for an opportunity."""
        prompt = f"""Suggest a specific action for this opportunity:

Title: {opportunity.title}
Description: {opportunity.description[:300]}
Source: {opportunity.source}

Return a JSON object with:
- type: comment, post, read, reach_out, or save_for_later
- title: short action title
- description: 1-2 sentence description
- priority: high, medium, or low"""
        
        response = await self.ai.complete(prompt, temperature=0.3, max_tokens=200)
        
        # Parse JSON
        import json
        import re
        try:
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return {
            "type": "read",
            "title": f"Read: {opportunity.title}",
            "description": opportunity.description[:150],
            "priority": "medium",
        }
    
    async def _generate_reflection(self, memories) -> str:
        """Generate reflection question."""
        memory_text = "\n".join([
            f"- {m.content[:150]}"
            for m in memories[:5]
        ]) or "No recent work"
        
        prompt = f"""Based on this recent work:
{memory_text}

Generate one thoughtful reflection question to help think about career positioning.
The question should prompt insight about achievements, impact, or expertise.
Keep it to one sentence."""
        
        return await self.ai.complete(prompt, temperature=0.7, max_tokens=100)
    
    async def _calculate_metrics(self, user_id: str) -> dict:
        """Calculate daily metrics."""
        today = utcnow().date()
        
        # Count events today
        events_result = await self.session.execute(
            select(func.count(Event.id))
            .where(Event.user_id == user_id)
            .where(func.date(Event.created_at) == today)
        )
        events_count = events_result.scalar() or 0
        
        # Count opportunities found
        opps_result = await self.session.execute(
            select(func.count(Opportunity.id))
            .where(Opportunity.user_id == user_id)
            .where(func.date(Opportunity.created_at) == today)
        )
        opps_count = opps_result.scalar() or 0
        
        # Count drafts created
        drafts_result = await self.session.execute(
            select(func.count(Draft.id))
            .where(Draft.user_id == user_id)
            .where(func.date(Draft.created_at) == today)
        )
        drafts_count = drafts_result.scalar() or 0
        
        return {
            "events_logged": events_count,
            "opportunities_found": opps_count,
            "drafts_created": drafts_count,
        }
    
    async def _save_briefing(self, user_id: str, briefing: Briefing):
        """Save briefing to database."""
        db_summary = DailySummary(
            id=generate_id(),
            user_id=user_id,
            date=utcnow().date(),
            summary=briefing.summary,
            highlights=briefing.priorities,
            opportunities=[],
            actions_taken=[],
            metrics=briefing.metrics,
        )
        self.session.add(db_summary)
        await self.session.flush()


# Need to import func for count
from sqlalchemy import func
