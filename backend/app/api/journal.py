from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app.models.user import User
from app.models.journal import JournalEntry, SavedContent
from app.utils.token import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.get("/")
async def list_entries(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    entry_type: Optional[str] = None,
):
    q = select(JournalEntry).where(JournalEntry.user_id == user.id)
    if entry_type:
        q = q.where(JournalEntry.entry_type == entry_type)
    result = await db.execute(q.order_by(desc(JournalEntry.created_at)).offset(offset).limit(limit))
    entries = result.scalars().all()

    return [
        {
            "id": e.id,
            "content": e.content,
            "entry_type": e.entry_type,
            "source_url": e.source_url,
            "tags": e.tags,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


class JournalCreateRequest(BaseModel):
    content: str
    entry_type: str = "text"  # text, voice, meeting_note, idea, reflection
    source_url: str = None
    tags: list[str] = []
    title: str = None  # Optional title for meeting notes
    audio_data: str = None  # Base64 encoded audio for voice entries
    participants: list[str] = []  # For meeting notes
    duration_minutes: int = None  # For meeting notes


@router.post("/")
async def create_entry(
    req: JournalCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Auto-tag based on entry type
    tags = req.tags or []
    if req.entry_type == "voice" and "voice" not in tags:
        tags.append("voice")
    if req.entry_type == "meeting_note" and "meeting" not in tags:
        tags.append("meeting")
    if req.entry_type == "idea" and "idea" not in tags:
        tags.append("idea")

    # Build content with metadata for meeting notes
    content = req.content
    if req.entry_type == "meeting_note":
        parts = []
        if req.title:
            parts.append(f"Meeting: {req.title}")
        if req.participants:
            parts.append(f"Participants: {', '.join(req.participants)}")
        if req.duration_minutes:
            parts.append(f"Duration: {req.duration_minutes} min")
        parts.append(f"\n{content}")
        content = "\n".join(parts)

    entry = JournalEntry(
        user_id=user.id,
        content=content,
        entry_type=req.entry_type,
        source_url=req.source_url,
        tags=tags,
    )
    db.add(entry)
    await db.flush()

    from app.services.context_engine import ContextEngine
    engine = ContextEngine(db)
    await engine.ingest_from_journal(entry)

    try:
        from app.services.opportunity_radar import OpportunityRadar
        radar = OpportunityRadar(db)
        await radar.analyze_and_build_identity(user.id)
        await radar.find_opportunities(user.id)
    except Exception as e:
        logger.warning(f"Auto-opportunity generation after journal entry failed: {e}")

    return {
        "id": entry.id,
        "content": entry.content,
        "entry_type": entry.entry_type,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("/stats")
async def journal_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get journal statistics — streak, total entries, by type."""
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.user_id == user.id).order_by(desc(JournalEntry.created_at))
    )
    entries = result.scalars().all()

    type_counts = {}
    for e in entries:
        type_counts[e.entry_type] = type_counts.get(e.entry_type, 0) + 1

    # Calculate streak (consecutive days with entries)
    from datetime import date, timedelta
    entry_dates = set()
    for e in entries:
        if e.created_at:
            entry_dates.add(e.created_at.date())

    streak = 0
    today = date.today()
    check_date = today
    while check_date in entry_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return {
        "total": len(entries),
        "by_type": type_counts,
        "streak_days": streak,
        "has_entries_today": today in entry_dates,
    }


@router.get("/content")
async def list_saved_content(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
):
    result = await db.execute(
        select(SavedContent)
        .where(SavedContent.user_id == user.id)
        .order_by(desc(SavedContent.created_at))
        .limit(limit)
    )
    items = result.scalars().all()

    return [
        {
            "id": s.id,
            "url": s.url,
            "title": s.title,
            "excerpt": s.excerpt,
            "notes": s.notes,
            "tags": s.tags,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in items
    ]


class SavedContentCreateRequest(BaseModel):
    url: str
    title: str = None
    excerpt: str = None
    notes: str = None
    tags: list[str] = []


@router.post("/content")
async def create_saved_content(
    req: SavedContentCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = SavedContent(
        user_id=user.id,
        url=req.url,
        title=req.title,
        excerpt=req.excerpt,
        notes=req.notes,
        tags=req.tags,
    )
    db.add(item)
    await db.flush()

    from app.services.context_engine import ContextEngine
    engine = ContextEngine(db)
    await engine.ingest_saved_content(item)

    return {
        "id": item.id,
        "url": item.url,
        "title": item.title,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
