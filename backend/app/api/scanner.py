"""
Scanner API — LinkedIn post scanning, trend discovery, and daily briefings.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.token import get_current_user_id
from app.services.linkedin_scanner import LinkedInScanner
from app.services.trend_scanner import TrendScanner
from app.services.linkedin_api import LinkedInAPIService

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


class PostAnalysisRequest(BaseModel):
    url: str


class TrendScanRequest(BaseModel):
    topic: Optional[str] = None


class NewsScanRequest(BaseModel):
    query: Optional[str] = None


@router.post("/analyze-post")
async def analyze_linkedin_post(
    req: PostAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a LinkedIn post URL — extracts insights and suggests a comment."""
    scanner = LinkedInScanner(db)
    result = await scanner.analyze_post_url(user_id, req.url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/scan-opportunities")
async def scan_engagement_opportunities(
    req: TrendScanRequest = TrendScanRequest(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Scan for posts where the user can add value."""
    scanner = LinkedInScanner(db)
    opportunities = await scanner.scan_for_opportunities(user_id, req.topic)
    return {"opportunities": opportunities}


@router.post("/generate-opportunities")
async def generate_opportunities(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate engagement opportunities based on user context."""
    scanner = LinkedInScanner(db)
    opportunities = await scanner.generate_opportunities(user_id)
    return {"opportunities": opportunities}


@router.get("/trends")
async def get_trends(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get trending topics in the user's industry."""
    scanner = TrendScanner(db)
    trends = await scanner.scan_trends(user_id)
    return {"trends": trends}


@router.get("/linkedin-trends")
async def get_linkedin_trends(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get trending LinkedIn topics in the user's space."""
    scanner = TrendScanner(db)
    trends = await scanner.get_linkedin_trends(user_id)
    return {"trends": trends}


@router.post("/scan-news")
async def scan_news(
    req: NewsScanRequest = NewsScanRequest(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Scan news sources for relevant articles."""
    scanner = TrendScanner(db)
    articles = await scanner.scan_news(user_id, req.query)
    return {"articles": articles}


@router.get("/daily-briefing")
async def get_daily_briefing(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's AI-powered daily briefing."""
    scanner = TrendScanner(db)
    briefing = await scanner.get_daily_briefing(user_id)
    return briefing


@router.get("/linkedin-profile")
async def get_linkedin_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get user's LinkedIn profile data."""
    service = LinkedInAPIService(db)
    profile = await service.get_user_profile(user_id)
    return profile


@router.get("/linkedin-connections")
async def get_linkedin_connections(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get user's LinkedIn connections list."""
    service = LinkedInAPIService(db)
    connections = await service.get_user_connections(user_id)
    return {"connections": connections}
