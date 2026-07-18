"""Event models."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field

from pros.src.utils import generate_id, utcnow


class EventType(str, Enum):
    """Event types."""
    
    # Context events
    MEETING = "meeting"
    RESEARCH = "research"
    ARTICLE_READ = "article_read"
    POST_CREATED = "post_created"
    COMMENT_MADE = "comment_made"
    PROJECT_UPDATE = "project_update"
    LEARNING = "learning"
    IDEA = "idea"
    ACHIEVEMENT = "achievement"
    FRUSTRATION = "frustration"
    CONVERSATION = "conversation"
    CONTENT_SAVED = "content_saved"
    
    # Opportunity events
    OPPORTUNITY_FOUND = "opportunity_found"
    DRAFT_GENERATED = "draft_generated"
    
    # System events
    SYNC_COMPLETED = "sync_completed"
    DAILY_SUMMARY = "daily_summary"


class EventSource(str, Enum):
    """Event sources."""
    
    CHROME_EXTENSION = "chrome_extension"
    REFLECTION = "reflection"
    CONNECTOR = "connector"
    API = "api"
    MANUAL = "manual"
    SYSTEM = "system"


class EventCreate(BaseModel):
    """Event creation schema."""
    
    type: EventType
    source: EventSource
    timestamp: Optional[datetime] = None
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    """Event schema."""
    
    id: str = Field(default_factory=generate_id)
    user_id: str
    type: EventType
    source: EventSource
    timestamp: datetime = Field(default_factory=utcnow)
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding_id: Optional[str] = None
    processed: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    
    model_config = {"from_attributes": True}
