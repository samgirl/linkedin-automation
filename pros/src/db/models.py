"""Database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Float, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pros.src.db.database import Base


def generate_uuid() -> str:
    """Generate a new UUID."""
    return str(uuid.uuid4())


class Event(Base):
    """Professional event."""
    
    __tablename__ = "events"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memories: Mapped[list["Memory"]] = relationship(back_populates="event")


class Memory(Base):
    """Professional memory."""
    
    __tablename__ = "memories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    frequency: Mapped[float] = mapped_column(Float, default=0.0)
    decay_rate: Mapped[float] = mapped_column(Float, default=0.01)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    event_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("events.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event: Mapped[Optional["Event"]] = relationship(back_populates="memories")
    relationships_as_source: Mapped[list["MemoryRelationship"]] = relationship(
        back_populates="source_memory",
        foreign_keys="MemoryRelationship.source_id",
    )
    relationships_as_target: Mapped[list["MemoryRelationship"]] = relationship(
        back_populates="target_memory",
        foreign_keys="MemoryRelationship.target_id",
    )


class MemoryRelationship(Base):
    """Relationship between memories."""
    
    __tablename__ = "memory_relationships"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("memories.id"), index=True)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("memories.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(50))
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_memory: Mapped["Memory"] = relationship(
        back_populates="relationships_as_source",
        foreign_keys=[source_id],
    )
    target_memory: Mapped["Memory"] = relationship(
        back_populates="relationships_as_target",
        foreign_keys=[target_id],
    )


class IdentityNode(Base):
    """Identity graph node."""
    
    __tablename__ = "identity_nodes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))
    data: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    edges_as_source: Mapped[list["IdentityEdge"]] = relationship(
        back_populates="source_node",
        foreign_keys="IdentityEdge.source_id",
    )
    edges_as_target: Mapped[list["IdentityEdge"]] = relationship(
        back_populates="target_node",
        foreign_keys="IdentityEdge.target_id",
    )


class IdentityEdge(Base):
    """Identity graph edge."""
    
    __tablename__ = "identity_edges"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("identity_nodes.id"), index=True)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("identity_nodes.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(50))
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_node: Mapped["IdentityNode"] = relationship(
        back_populates="edges_as_source",
        foreign_keys=[source_id],
    )
    target_node: Mapped["IdentityNode"] = relationship(
        back_populates="edges_as_target",
        foreign_keys=[target_id],
    )


class SavedContent(Base):
    """Content saved from Chrome extension."""
    
    __tablename__ = "saved_content"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    url: Mapped[str] = mapped_column(Text, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Opportunity(Base):
    """Discovered opportunity."""
    
    __tablename__ = "opportunities"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    scores: Mapped[dict] = mapped_column(JSON)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Draft(Base):
    """Generated content draft."""
    
    __tablename__ = "drafts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    topics: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    source_memories: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    source_evidence: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailySummary(Base):
    """Daily summary."""
    
    __tablename__ = "daily_summaries"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    content: Mapped[str] = mapped_column(Text)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConnectorState(Base):
    """External connector state."""
    
    __tablename__ = "connector_state"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    connector_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
