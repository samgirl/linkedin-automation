"""Events router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.core.events.service import EventsService
from pros.src.core.events.models import EventCreate, EventType, EventSource

router = APIRouter()


class EventResponse(BaseModel):
    """Event response schema."""
    id: str
    user_id: str
    type: str
    source: str
    timestamp: str
    title: Optional[str] = None
    content: Optional[str] = None
    processed: bool


class EventListResponse(BaseModel):
    """Event list response schema."""
    events: list[EventResponse]
    total: int


@router.post("/", response_model=EventResponse)
async def create_event(
    data: EventCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Create a new event."""
    service = EventsService(db)
    event = await service.create(user_id, data)
    
    return EventResponse(
        id=event.id,
        user_id=event.user_id,
        type=event.type.value,
        source=event.source.value,
        timestamp=event.timestamp.isoformat(),
        title=event.title,
        content=event.content,
        processed=event.processed,
    )


@router.get("/", response_model=EventListResponse)
async def list_events(
    event_type: Optional[EventType] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """List events for a user."""
    service = EventsService(db)
    events = await service.list(
        user_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    total = await service.count(user_id, event_type=event_type)
    
    return EventListResponse(
        events=[
            EventResponse(
                id=e.id,
                user_id=e.user_id,
                type=e.type.value,
                source=e.source.value,
                timestamp=e.timestamp.isoformat(),
                title=e.title,
                content=e.content,
                processed=e.processed,
            )
            for e in events
        ],
        total=total,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an event by ID."""
    service = EventsService(db)
    event = await service.get(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventResponse(
        id=event.id,
        user_id=event.user_id,
        type=event.type.value,
        source=event.source.value,
        timestamp=event.timestamp.isoformat(),
        title=event.title,
        content=event.content,
        processed=event.processed,
    )
