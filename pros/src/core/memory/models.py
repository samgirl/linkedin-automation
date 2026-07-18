"""Memory models."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field

from pros.src.utils import generate_id, utcnow


class MemoryType(str, Enum):
    """Memory types."""
    
    EPISODIC = "episodic"      # What happened
    SEMANTIC = "semantic"      # What they know
    PROCEDURAL = "procedural"  # How they work
    BELIEF = "belief"          # What they believe
    RELATIONAL = "relational"  # Who they know
    PATTERN = "pattern"        # What they do repeatedly


class MemoryCreate(BaseModel):
    """Memory creation schema."""
    
    type: MemoryType
    content: str
    summary: Optional[str] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    event_id: Optional[str] = None


class Memory(BaseModel):
    """Memory schema."""
    
    id: str = Field(default_factory=generate_id)
    user_id: str
    type: MemoryType
    content: str
    summary: Optional[str] = None
    importance: float = 0.5
    confidence: float = 0.5
    frequency: float = 0.0
    decay_rate: float = 0.01
    source: Optional[str] = None
    embedding_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    last_accessed: datetime = Field(default_factory=utcnow)
    access_count: int = 0
    archived: bool = False
    event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
    model_config = {"from_attributes": True}
