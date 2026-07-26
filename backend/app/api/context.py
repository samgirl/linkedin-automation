from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.context import Event, Memory, Identity
from app.utils.token import get_current_user

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("/memories")
async def get_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    q: str = Query(None, description="Search query"),
    type: str = Query(None, description="Memory type filter"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(Memory).where(Memory.user_id == user.id, Memory.archived == False)

    if type:
        query = query.where(Memory.type == type)

    if q:
        query = query.where(Memory.content.ilike(f"%{q}%"))

    query = query.order_by(desc(Memory.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    memories = result.scalars().all()

    return [
        {
            "id": m.id,
            "type": m.type,
            "content": m.content,
            "summary": m.summary,
            "importance": m.importance,
            "confidence": m.confidence,
            "tags": m.tags,
            "source": m.source,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memories
    ]


@router.get("/identity")
async def get_identity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Identity).where(Identity.user_id == user.id).order_by(desc(Identity.confidence))
    )
    nodes = result.scalars().all()

    return [
        {
            "id": n.id,
            "type": n.type,
            "name": n.name,
            "data": n.data,
            "confidence": n.confidence,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in nodes
    ]


@router.get("/timeline")
async def get_timeline(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Event)
        .where(Event.user_id == user.id)
        .order_by(desc(Event.created_at))
        .offset(offset)
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        {
            "id": e.id,
            "type": e.type,
            "source": e.source,
            "title": e.title,
            "content": e.content[:500] if e.content else None,
            "metadata": e.extra_data,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


class ContextQueryRequest(BaseModel):
    query: str
    limit: int = 10


@router.post("/query")
async def query_context(
    req: ContextQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.vector_store import VectorStore
    vs = VectorStore()
    content_results = await vs.search(user.id, req.query, n_results=req.limit)

    memories = [
        {"content": text, "type": "memory"}
        for text in content_results
        if text
    ]

    return {"results": memories, "query": req.query}
