"""Daily briefing API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.briefing.generator import DailyBriefingGenerator

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/daily")
async def get_daily_briefing(
    db: AsyncSession = Depends(get_db),
):
    """Get daily briefing."""
    generator = DailyBriefingGenerator(db)
    
    briefing = await generator.generate("default_user")
    
    return {
        "date": briefing.date,
        "summary": briefing.summary,
        "priorities": briefing.priorities,
        "opportunities": briefing.opportunities,
        "suggested_actions": briefing.suggested_actions,
        "reflection_question": briefing.reflection_question,
        "metrics": briefing.metrics,
    }


@router.get("/today")
async def get_today_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get today's summary."""
    from pros.src.db.models import DailySummary
    from sqlalchemy import select
    from pros.src.utils import utcnow
    
    today = utcnow().date()
    
    result = await db.execute(
        select(DailySummary)
        .where(DailySummary.date == today)
        .limit(1)
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        return {"message": "No summary for today yet. Run daily briefing first."}
    
    return {
        "date": summary.date.isoformat(),
        "summary": summary.summary,
        "highlights": summary.highlights,
        "metrics": summary.metrics,
    }
