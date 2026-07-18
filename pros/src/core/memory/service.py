"""Memory service."""

import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.models import Memory as MemoryModel
from pros.src.core.memory.models import Memory, MemoryCreate, MemoryType
from pros.src.utils import generate_id, utcnow


# Decay rates by memory type
DECAY_RATES = {
    MemoryType.BELIEF.value: 0.003,
    MemoryType.SEMANTIC.value: 0.005,
    MemoryType.PROCEDURAL.value: 0.008,
    MemoryType.EPISODIC.value: 0.01,
    MemoryType.RELATIONAL.value: 0.015,
    MemoryType.PATTERN.value: 0.01,
}


class MemoryService:
    """Memory service for managing professional memories."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user_id: str, data: MemoryCreate) -> Memory:
        """Create a new memory."""
        memory = MemoryModel(
            id=generate_id(),
            user_id=user_id,
            type=data.type.value,
            content=data.content,
            summary=data.summary,
            importance=data.importance,
            confidence=data.confidence,
            decay_rate=DECAY_RATES.get(data.type.value, 0.01),
            source=data.source,
            tags=data.tags,
            metadata_=data.metadata,
            event_id=data.event_id,
        )
        
        self.session.add(memory)
        await self.session.flush()
        
        return Memory.model_validate(memory)
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        result = await self.session.execute(
            select(MemoryModel).where(MemoryModel.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if memory:
            # Update access stats
            memory.access_count += 1
            memory.last_accessed = utcnow()
            
        return Memory.model_validate(memory) if memory else None
    
    async def list(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Memory]:
        """List memories for a user."""
        query = select(MemoryModel).where(MemoryModel.user_id == user_id)
        
        if memory_type:
            query = query.where(MemoryModel.type == memory_type.value)
        
        if min_importance > 0:
            query = query.where(MemoryModel.importance >= min_importance)
        
        if not include_archived:
            query = query.where(MemoryModel.archived == False)
        
        query = query.order_by(MemoryModel.importance.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        memories = result.scalars().all()
        
        return [Memory.model_validate(m) for m in memories]
    
    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> list[Memory]:
        """Search memories by content (simple text search)."""
        search_query = f"%{query}%"
        
        query = (
            select(MemoryModel)
            .where(MemoryModel.user_id == user_id)
            .where(MemoryModel.content.ilike(search_query))
            .where(MemoryModel.archived == False)
            .order_by(MemoryModel.importance.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        memories = result.scalars().all()
        
        return [Memory.model_validate(m) for m in memories]
    
    async def update_importance(self, memory_id: str, delta: float) -> Optional[Memory]:
        """Update memory importance."""
        result = await self.session.execute(
            select(MemoryModel).where(MemoryModel.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if memory:
            memory.importance = max(0.0, min(1.0, memory.importance + delta))
            memory.updated_at = utcnow()
            
        return Memory.model_validate(memory) if memory else None
    
    async def apply_decay(self, user_id: Optional[str] = None) -> int:
        """Apply decay to all memories. Returns count of affected memories."""
        now = utcnow()
        
        query = select(MemoryModel).where(MemoryModel.archived == False)
        if user_id:
            query = query.where(MemoryModel.user_id == user_id)
        
        result = await self.session.execute(query)
        memories = result.scalars().all()
        
        affected = 0
        for memory in memories:
            days_since_access = (now - memory.last_accessed).days
            if days_since_access <= 0:
                continue
            
            decay_rate = memory.decay_rate
            decay_factor = math.exp(-decay_rate * days_since_access)
            new_importance = memory.importance * decay_factor
            
            # Floor at 0.01
            new_importance = max(0.01, new_importance)
            
            if abs(new_importance - memory.importance) > 0.001:
                memory.importance = new_importance
                affected += 1
            
            # Archive if importance very low and not accessed in 6 months
            if new_importance < 0.1 and days_since_access > 180:
                memory.archived = True
                affected += 1
        
        return affected
    
    async def count(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None,
    ) -> int:
        """Count memories for a user."""
        query = select(func.count()).select_from(MemoryModel).where(
            MemoryModel.user_id == user_id
        )
        
        if memory_type:
            query = query.where(MemoryModel.type == memory_type.value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
