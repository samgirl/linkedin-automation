from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.opportunity import Draft
from app.utils.token import get_current_user

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("/")
async def list_drafts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Draft).where(Draft.user_id == user.id)
    if status:
        query = query.where(Draft.status == status)
    query = query.order_by(desc(Draft.created_at)).limit(limit)

    result = await db.execute(query)
    drafts = result.scalars().all()

    return [
        {
            "id": d.id,
            "type": d.type,
            "title": d.title,
            "content": d.content,
            "status": d.status,
            "platform": d.platform,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "published_at": d.published_at.isoformat() if d.published_at else None,
        }
        for d in drafts
    ]


@router.get("/{draft_id}")
async def get_draft(
    draft_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {
        "id": draft.id,
        "type": draft.type,
        "title": draft.title,
        "content": draft.content,
        "status": draft.status,
        "platform": draft.platform,
        "metadata": draft.extra_data,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
        "published_at": draft.published_at.isoformat() if draft.published_at else None,
    }


class DraftUpdateRequest(BaseModel):
    content: str = None
    title: str = None
    status: str = None


@router.put("/{draft_id}")
async def update_draft(
    draft_id: str,
    req: DraftUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if req.content is not None:
        draft.content = req.content
    if req.title is not None:
        draft.title = req.title
    if req.status is not None:
        draft.status = req.status

    return {"status": "updated", "id": draft.id}


@router.post("/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Draft).where(Draft.id == draft_id, Draft.user_id == user.id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    from app.utils.helpers import utcnow
    draft.status = "published"
    draft.published_at = utcnow()

    return {"status": "published", "id": draft.id, "published_at": draft.published_at.isoformat()}
