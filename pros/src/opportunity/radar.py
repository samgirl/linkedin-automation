"""Opportunity Radar - scans the outside world and surfaces what matters."""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.models import Opportunity as OpportunityModel
from pros.src.opportunity.scanners.base import BaseScanner, ScanResult
from pros.src.opportunity.scanners.linkedin import LinkedInScanner
from pros.src.opportunity.scanners.github import GitHubScanner
from pros.src.opportunity.scanners.rss import RSSScanner
from pros.src.opportunity.scanners.arxiv import ArxivScanner
from pros.src.opportunity.rankers.relevance import RelevanceRanker
from pros.src.ai.orchestrator import get_ai
from pros.src.utils import generate_id, utcnow


class OpportunityRadar:
    """Scans external sources and surfaces opportunities."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai = get_ai()
        self.ranker = RelevanceRanker(session)
        self.scanners: list[BaseScanner] = [
            LinkedInScanner(),
            GitHubScanner(),
            RSSScanner(),
            ArxivScanner(),
        ]
    
    async def scan(
        self,
        user_id: str,
        sources: Optional[list[str]] = None,
    ) -> list[dict]:
        """Scan specified sources for opportunities."""
        results = []
        
        for scanner in self.scanners:
            if sources and scanner.name not in sources:
                continue
            
            try:
                scan_results = await scanner.scan(user_id)
                results.extend(scan_results)
            except Exception as e:
                print(f"Scanner {scanner.name} failed: {e}")
                continue
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)
        
        return unique_results
    
    async def rank(
        self,
        user_id: str,
        opportunities: list[dict],
    ) -> list[dict]:
        """Rank opportunities by relevance."""
        ranked = []
        
        for opp in opportunities:
            score = await self.ranker.score(user_id, opp)
            opp["score"] = score
            ranked.append(opp)
        
        # Sort by score descending
        ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return ranked
    
    async def save(
        self,
        user_id: str,
        opportunities: list[dict],
    ) -> list[dict]:
        """Save opportunities to database."""
        saved = []
        
        for opp in opportunities:
            db_opp = OpportunityModel(
                id=generate_id(),
                user_id=user_id,
                title=opp.get("title", "Untitled"),
                description=opp.get("description", ""),
                source=opp.get("source"),
                source_url=opp.get("url"),
                topics=opp.get("topics", []),
                scores={"relevance": opp.get("score", 0)},
                recommended_action=opp.get("recommended_action"),
                reasoning=opp.get("reasoning"),
                status="pending",
            )
            self.session.add(db_opp)
            saved.append(opp)
        
        await self.session.flush()
        return saved
    
    async def get_daily_briefing(self, user_id: str) -> dict:
        """Generate daily briefing with top opportunities."""
        # Get recent opportunities
        result = await self.session.execute(
            select(OpportunityModel)
            .where(OpportunityModel.user_id == user_id)
            .where(OpportunityModel.status == "pending")
            .order_by(OpportunityModel.created_at.desc())
            .limit(20)
        )
        opportunities = result.scalars().all()
        
        if not opportunities:
            return {
                "summary": "No new opportunities found today.",
                "top_opportunities": [],
                "suggested_actions": [],
            }
        
        # Generate briefing
        opp_text = "\n".join([
            f"- {o.title}: {o.description[:100]}"
            for o in opportunities[:10]
        ])
        
        prompt = f"""Generate a concise daily briefing for a professional.

Recent opportunities found:
{opp_text}

Create a briefing that:
1. Summarizes the top 3-5 opportunities
2. Explains why each matters
3. Suggests specific actions (comment, post, read, reach out)
4. Keeps total under 300 words

Write in a helpful coworker tone."""

        summary = await self.ai.complete(prompt, temperature=0.7, max_tokens=500)
        
        return {
            "summary": summary,
            "top_opportunities": [
                {
                    "title": o.title,
                    "description": o.description[:200],
                    "source": o.source,
                    "score": o.scores.get("relevance", 0) if o.scores else 0,
                }
                for o in opportunities[:5]
            ],
            "generated_at": utcnow().isoformat(),
        }


# Need to import select
from sqlalchemy import select
