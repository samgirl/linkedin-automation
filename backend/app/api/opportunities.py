from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.opportunity import Opportunity, Draft
from app.utils.token import get_current_user

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("/")
async def list_opportunities(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str = Query("pending", description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.user_id == user.id, Opportunity.status == status)
        .order_by(desc(Opportunity.created_at))
        .limit(limit)
    )
    opps = result.scalars().all()

    return [
        {
            "id": o.id,
            "type": o.type,
            "title": o.title,
            "description": o.description,
            "source_url": o.source_url,
            "source_author": o.source_author,
            "topics": o.topics,
            "scores": o.scores,
            "recommended_action": o.recommended_action,
            "reasoning": o.reasoning,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in opps
    ]


@router.post("/{opportunity_id}/dismiss")
async def dismiss_opportunity(
    opportunity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.user_id == user.id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = "dismissed"
    return {"status": "dismissed"}


@router.post("/{opportunity_id}/complete")
async def complete_opportunity(
    opportunity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.user_id == user.id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = "completed"
    return {"status": "completed"}


class DraftGenerateRequest(BaseModel):
    opportunity_id: str = None
    type: str = "post"
    topic: str = ""
    extra_context: str = ""


@router.post("/{opportunity_id}/draft")
async def generate_draft(
    opportunity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id, Opportunity.user_id == user.id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    from app.services.content_generator import ContentGenerator
    gen = ContentGenerator(db)
    draft = await gen.generate_for_opportunity(user.id, opp)

    return {
        "id": draft.id,
        "type": draft.type,
        "content": draft.content,
        "status": draft.status,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.post("/generate")
async def generate_standalone_draft(
    req: DraftGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.content_generator import ContentGenerator
    gen = ContentGenerator(db)
    draft = await gen.generate_standalone(user.id, req.type, req.topic, req.extra_context)

    return {
        "id": draft.id,
        "type": draft.type,
        "content": draft.content,
        "status": draft.status,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }
