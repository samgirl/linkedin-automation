"""Opportunity Radar API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from pros.src.db.database import get_db
from pros.src.db.models import Opportunity
from pros.src.opportunity.radar import OpportunityRadar

router = APIRouter(prefix="/opportunity", tags=["opportunity"])


@router.get("/")
async def list_opportunities(
    status: str = "pending",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List opportunities."""
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.status == status)
        .order_by(Opportunity.created_at.desc())
        .limit(limit)
    )
    opportunities = result.scalars().all()
    
    return [
        {
            "id": o.id,
            "title": o.title,
            "description": o.description,
            "source": o.source,
            "score": o.scores.get("relevance", 0) if o.scores else 0,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in opportunities
    ]


@router.post("/scan")
async def scan_opportunities(
    sources: list[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Scan for new opportunities."""
    radar = OpportunityRadar(db)
    
    results = await radar.scan("default_user", sources)
    ranked = await radar.rank("default_user", results)
    saved = await radar.save("default_user", ranked)
    
    return {
        "scanned": len(results),
        "saved": len(saved),
        "top_opportunities": ranked[:5],
    }


@router.post("/{opportunity_id}/save")
async def save_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Save/mark opportunity as read."""
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opportunity.status = "saved"
    await db.commit()
    
    return {"message": "Opportunity saved"}


@router.post("/{opportunity_id}/dismiss")
async def dismiss_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Dismiss opportunity."""
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opportunity.status = "dismissed"
    await db.commit()
    
    return {"message": "Opportunity dismissed"}
