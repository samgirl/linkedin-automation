"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KeywordSchema(BaseModel):
    id: Optional[int] = None
    term: str
    domain: str
    weight: float = 1.0
    is_custom: bool = False
    aliases: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)


class DomainSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: str = ""
    is_active: bool = True


class PostSchema(BaseModel):
    id: Optional[int] = None
    url: str
    title: str = ""
    text: str
    author_name: str = ""
    author_title: str = ""
    author_url: str = ""
    organization: str = ""
    date_posted: Optional[datetime] = None
    date_collected: Optional[datetime] = None
    engagement_likes: int = 0
    engagement_comments: int = 0
    engagement_shares: int = 0
    media_images: list[str] = Field(default_factory=list)
    media_videos: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    mentioned_companies: list[str] = Field(default_factory=list)
    mentioned_orgs: list[str] = Field(default_factory=list)
    mentioned_tech: list[str] = Field(default_factory=list)
    source: str = "linkedin"
    is_duplicate: bool = False
    raw_data: dict = Field(default_factory=dict)


class RankingSchema(BaseModel):
    id: Optional[int] = None
    post_id: int
    score: int = 0
    reason: str = ""
    keyword_match_score: float = 0.0
    semantic_score: float = 0.0
    quality_score: float = 0.0
    freshness_score: float = 0.0
    engagement_score: float = 0.0
    novelty_score: float = 0.0
    opportunity_score: float = 0.0
    ranked_at: Optional[datetime] = None


class CommentSchema(BaseModel):
    id: Optional[int] = None
    post_id: int
    comment_type: str = "professional"
    text: str
    word_count: int = 0
    is_approved: bool = False
    is_edited: bool = False
    is_copied: bool = False
    generated_at: Optional[datetime] = None
    model_used: str = ""
    prompt_version: str = ""


class SearchHistorySchema(BaseModel):
    id: Optional[int] = None
    query: str
    domains: list[str] = Field(default_factory=list)
    keywords_used: list[str] = Field(default_factory=list)
    results_count: int = 0
    avg_score: float = 0.0
    searched_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class UserActionSchema(BaseModel):
    id: Optional[int] = None
    post_id: int
    comment_id: Optional[int] = None
    action: str  # approved, rejected, favorite, copied, ignored, edited
    timestamp: Optional[datetime] = None
    notes: str = ""


class PersonalKnowledgeSchema(BaseModel):
    id: Optional[int] = None
    category: str  # project, industry, technology, interest, background
    key: str
    value: str
    relevance_weight: float = 1.0
    created_at: Optional[datetime] = None


class CacheEntrySchema(BaseModel):
    id: Optional[int] = None
    cache_key: str
    cache_type: str  # search, embedding, comment, ranking
    data: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
