"""Content generation API routes."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.content.generator import ContentGenerator, ContentRequest

router = APIRouter(prefix="/api/content", tags=["content"])


class GenerateRequest(BaseModel):
    """Content generation request."""
    content_type: str  # post, comment, article, thread
    topic: str
    context: Optional[str] = None
    tone: str = "professional"
    length: str = "medium"
    include_opportunities: bool = False


class LinkedInPostRequest(BaseModel):
    """LinkedIn post generation request."""
    topic: str
    include_opportunities: bool = False


class LinkedInCommentRequest(BaseModel):
    """LinkedIn comment generation request."""
    post_url: str
    post_content: str


class ArticleRequest(BaseModel):
    """Article generation request."""
    topic: str
    outline: Optional[str] = None


class ThreadRequest(BaseModel):
    """Thread generation request."""
    topic: str
    num_tweets: int = 5


@router.post("/generate")
async def generate_content(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate content based on request."""
    generator = ContentGenerator(db)
    
    content_request = ContentRequest(
        content_type=request.content_type,
        topic=request.topic,
        context=request.context,
        tone=request.tone,
        length=request.length,
        include_opportunities=request.include_opportunities,
    )
    
    result = await generator.generate("default_user", content_request)
    
    return {
        "content_type": result.content_type,
        "title": result.title,
        "body": result.body,
        "topics": result.topics,
        "metadata": result.metadata,
    }


@router.post("/linkedin/post")
async def generate_linkedin_post(
    request: LinkedInPostRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a LinkedIn post."""
    generator = ContentGenerator(db)
    
    result = await generator.generate_linkedin_post(
        "default_user",
        request.topic,
        request.include_opportunities,
    )
    
    return {
        "title": result.title,
        "body": result.body,
        "topics": result.topics,
    }


@router.post("/linkedin/comment")
async def generate_linkedin_comment(
    request: LinkedInCommentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a LinkedIn comment."""
    generator = ContentGenerator(db)
    
    result = await generator.generate_linkedin_comment(
        "default_user",
        request.post_url,
        request.post_content,
    )
    
    return {
        "body": result.body,
    }


@router.post("/article")
async def generate_article(
    request: ArticleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate an article."""
    generator = ContentGenerator(db)
    
    result = await generator.generate_article(
        "default_user",
        request.topic,
        request.outline,
    )
    
    return {
        "title": result.title,
        "body": result.body,
        "topics": result.topics,
    }


@router.post("/thread")
async def generate_thread(
    request: ThreadRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a thread."""
    generator = ContentGenerator(db)
    
    result = await generator.generate_thread(
        "default_user",
        request.topic,
        request.num_tweets,
    )
    
    return {
        "title": result.title,
        "body": result.body,
    }
