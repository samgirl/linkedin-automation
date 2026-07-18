"""Identity models."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field

from pros.src.utils import generate_id, utcnow


class NodeType(str, Enum):
    """Identity node types."""
    
    PERSON = "person"
    PROJECT = "project"
    SKILL = "skill"
    TECHNOLOGY = "technology"
    INDUSTRY = "industry"
    TOPIC = "topic"
    BELIEF = "belief"
    GOAL = "goal"
    INTEREST = "interest"
    COMPANY = "company"
    STYLE = "style"


class RelationshipType(str, Enum):
    """Identity edge types."""
    
    WORKS_ON = "works_on"
    HAS_SKILL = "has_skill"
    USES_TECH = "uses_tech"
    INTERESTED_IN = "interested_in"
    BELIEVES = "believes"
    GOAL_ALIGNED = "goal_aligned"
    COLLABORATES_WITH = "collaborates_with"
    EXPERT_IN = "expert_in"
    LEARNING = "learning"
    WRITES_ABOUT = "writes_about"


class IdentityNodeCreate(BaseModel):
    """Identity node creation schema."""
    
    type: NodeType
    name: str
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdentityNode(BaseModel):
    """Identity node schema."""
    
    id: str = Field(default_factory=generate_id)
    user_id: str
    type: NodeType
    name: str
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    embedding_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    
    model_config = {"from_attributes": True}


class IdentityEdgeCreate(BaseModel):
    """Identity edge creation schema."""
    
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdentityEdge(BaseModel):
    """Identity edge schema."""
    
    id: str = Field(default_factory=generate_id)
    user_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = 0.5
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    
    model_config = {"from_attributes": True}


class Identity(BaseModel):
    """Complete identity snapshot."""
    
    nodes: list[IdentityNode] = Field(default_factory=list)
    edges: list[IdentityEdge] = Field(default_factory=list)
    
    @property
    def projects(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.PROJECT]
    
    @property
    def skills(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.SKILL]
    
    @property
    def topics(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.TOPIC]
    
    @property
    def beliefs(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.BELIEF]
    
    @property
    def goals(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.GOAL]
    
    @property
    def interests(self) -> list[IdentityNode]:
        return [n for n in self.nodes if n.type == NodeType.INTEREST]
