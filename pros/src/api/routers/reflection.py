"""Reflection API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.core.reflection.service import ReflectionService

router = APIRouter(prefix="/reflection", tags=["reflection"])


@router.post("/daily")
async def generate_daily_reflection(
    db: AsyncSession = Depends(get_db),
):
    """Generate daily reflection."""
    service = ReflectionService(db)
    
    reflection = await service.generate_daily_reflection("default_user")
    
    return {
        "id": reflection.id,
        "questions": reflection.questions,
        "insights": reflection.insights,
        "score": reflection.score,
        "metrics": reflection.metrics,
    }


@router.get("/questions")
async def get_reflection_questions(
    db: AsyncSession = Depends(get_db),
):
    """Get reflection questions."""
    service = ReflectionService(db)
    
    questions = await service.generate_questions("default_user")
    
    return {"questions": questions}
