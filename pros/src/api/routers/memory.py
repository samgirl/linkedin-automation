"""Memory router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.core.memory.service import MemoryService
from pros.src.core.memory.models import MemoryCreate, MemoryType

router = APIRouter()


class MemoryResponse(BaseModel):
    """Memory response schema."""
    id: str
    user_id: str
    type: str
    content: str
    summary: Optional[str] = None
    importance: float
    confidence: float
    tags: list[str]


class MemoryListResponse(BaseModel):
    """Memory list response schema."""
    memories: list[MemoryResponse]
    total: int


class SearchRequest(BaseModel):
    """Search request schema."""
    query: str
    limit: int = 10


@router.post("/", response_model=MemoryResponse)
async def create_memory(
    data: MemoryCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Create a new memory."""
    service = MemoryService(db)
    memory = await service.create(user_id, data)
    
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        type=memory.type.value,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        confidence=memory.confidence,
        tags=memory.tags,
    )


@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    memory_type: Optional[MemoryType] = None,
    min_importance: float = 0.0,
    limit: int = 50,
    offset: int = 0,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """List memories for a user."""
    service = MemoryService(db)
    memories = await service.list(
        user_id,
        memory_type=memory_type,
        min_importance=min_importance,
        limit=limit,
        offset=offset,
    )
    total = await service.count(user_id, memory_type=memory_type)
    
    return MemoryListResponse(
        memories=[
            MemoryResponse(
                id=m.id,
                user_id=m.user_id,
                type=m.type.value,
                content=m.content,
                summary=m.summary,
                importance=m.importance,
                confidence=m.confidence,
                tags=m.tags,
            )
            for m in memories
        ],
        total=total,
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a memory by ID."""
    service = MemoryService(db)
    memory = await service.get(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        type=memory.type.value,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        confidence=memory.confidence,
        tags=memory.tags,
    )


@router.post("/search", response_model=MemoryListResponse)
async def search_memories(
    data: SearchRequest,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Search memories by content."""
    service = MemoryService(db)
    memories = await service.search(user_id, data.query, data.limit)
    
    return MemoryListResponse(
        memories=[
            MemoryResponse(
                id=m.id,
                user_id=m.user_id,
                type=m.type.value,
                content=m.content,
                summary=m.summary,
                importance=m.importance,
                confidence=m.confidence,
                tags=m.tags,
            )
            for m in memories
        ],
        total=len(memories),
    )


@router.post("/decay")
async def apply_decay(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Apply memory decay."""
    service = MemoryService(db)
    affected = await service.apply_decay(user_id)
    
    return {"affected": affected}
