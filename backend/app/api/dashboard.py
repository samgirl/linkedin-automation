from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.user import User
from app.models.context import Event, Memory
from app.models.opportunity import Opportunity
from app.models.journal import JournalEntry
from app.utils.token import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/briefing")
async def get_briefing(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.content_generator import ContentGenerator
    gen = ContentGenerator(db)
    briefing = await gen.generate_briefing(user.id)

    return briefing


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event_count = await db.execute(
        select(func.count(Event.id)).where(Event.user_id == user.id)
    )
    memory_count = await db.execute(
        select(func.count(Memory.id)).where(Memory.user_id == user.id, Memory.archived == False)
    )
    pending_opps = await db.execute(
        select(func.count(Opportunity.id)).where(Opportunity.user_id == user.id, Opportunity.status == "pending")
    )
    journal_count = await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.user_id == user.id)
    )

    return {
        "total_events": event_count.scalar() or 0,
        "total_memories": memory_count.scalar() or 0,
        "pending_opportunities": pending_opps.scalar() or 0,
        "journal_entries": journal_count.scalar() or 0,
    }
