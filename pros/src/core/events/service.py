"""Events service."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.models import Event as EventModel
from pros.src.core.events.models import Event, EventCreate, EventType, EventSource
from pros.src.utils import generate_id, utcnow


class EventsService:
    """Events service for managing professional events."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user_id: str, data: EventCreate) -> Event:
        """Create a new event."""
        event = EventModel(
            id=generate_id(),
            user_id=user_id,
            type=data.type.value,
            source=data.source.value,
            timestamp=data.timestamp or utcnow(),
            title=data.title,
            content=data.content,
            metadata_=data.metadata,
        )
        
        self.session.add(event)
        await self.session.flush()
        
        return Event.model_validate(event)
    
    async def get(self, event_id: str) -> Optional[Event]:
        """Get an event by ID."""
        result = await self.session.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        event = result.scalar_one_or_none()
        return Event.model_validate(event) if event else None
    
    async def list(
        self,
        user_id: str,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        """List events for a user."""
        query = select(EventModel).where(EventModel.user_id == user_id)
        
        if event_type:
            query = query.where(EventModel.type == event_type.value)
        if start_date:
            query = query.where(EventModel.timestamp >= start_date)
        if end_date:
            query = query.where(EventModel.timestamp <= end_date)
        
        query = query.order_by(EventModel.timestamp.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        return [Event.model_validate(e) for e in events]
    
    async def count(
        self,
        user_id: str,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count events for a user."""
        query = select(func.count()).select_from(EventModel).where(
            EventModel.user_id == user_id
        )
        
        if event_type:
            query = query.where(EventModel.type == event_type.value)
        if start_date:
            query = query.where(EventModel.timestamp >= start_date)
        if end_date:
            query = query.where(EventModel.timestamp <= end_date)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def mark_processed(self, event_id: str) -> None:
        """Mark an event as processed."""
        result = await self.session.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.processed = True
    
    async def get_unprocessed(self, limit: int = 100) -> list[Event]:
        """Get unprocessed events."""
        query = (
            select(EventModel)
            .where(EventModel.processed == False)
            .order_by(EventModel.timestamp.asc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        return [Event.model_validate(e) for e in events]
