"""Identity router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.database import get_db
from pros.src.core.identity.service import IdentityService
from pros.src.core.identity.models import (
    IdentityNodeCreate,
    IdentityEdgeCreate,
    NodeType,
    RelationshipType,
)

router = APIRouter()


class NodeResponse(BaseModel):
    """Node response schema."""
    id: str
    user_id: str
    type: str
    name: str
    data: dict
    confidence: float


class EdgeResponse(BaseModel):
    """Edge response schema."""
    id: str
    user_id: str
    source_id: str
    target_id: str
    relationship_type: str
    strength: float


class IdentityResponse(BaseModel):
    """Identity response schema."""
    nodes: list[NodeResponse]
    edges: list[EdgeResponse]


@router.post("/nodes", response_model=NodeResponse)
async def create_node(
    data: IdentityNodeCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Create a new identity node."""
    service = IdentityService(db)
    node = await service.create_node(user_id, data)
    
    return NodeResponse(
        id=node.id,
        user_id=node.user_id,
        type=node.type.value,
        name=node.name,
        data=node.data,
        confidence=node.confidence,
    )


@router.get("/nodes", response_model=list[NodeResponse])
async def list_nodes(
    node_type: Optional[NodeType] = None,
    limit: int = 100,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """List identity nodes."""
    service = IdentityService(db)
    nodes = await service.list_nodes(user_id, node_type, limit)
    
    return [
        NodeResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type.value,
            name=n.name,
            data=n.data,
            confidence=n.confidence,
        )
        for n in nodes
    ]


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a node by ID."""
    service = IdentityService(db)
    node = await service.get_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return NodeResponse(
        id=node.id,
        user_id=node.user_id,
        type=node.type.value,
        name=node.name,
        data=node.data,
        confidence=node.confidence,
    )


@router.post("/edges", response_model=EdgeResponse)
async def create_edge(
    data: IdentityEdgeCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Create a new identity edge."""
    service = IdentityService(db)
    edge = await service.create_edge(user_id, data)
    
    return EdgeResponse(
        id=edge.id,
        user_id=edge.user_id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        relationship_type=edge.relationship_type.value,
        strength=edge.strength,
    )


@router.get("/", response_model=IdentityResponse)
async def get_identity(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Get complete identity."""
    service = IdentityService(db)
    identity = await service.get_identity(user_id)
    
    return IdentityResponse(
        nodes=[
            NodeResponse(
                id=n.id,
                user_id=n.user_id,
                type=n.type.value,
                name=n.name,
                data=n.data,
                confidence=n.confidence,
            )
            for n in identity.nodes
        ],
        edges=[
            EdgeResponse(
                id=e.id,
                user_id=e.user_id,
                source_id=e.source_id,
                target_id=e.target_id,
                relationship_type=e.relationship_type.value,
                strength=e.strength,
            )
            for e in identity.edges
        ],
    )


@router.get("/nodes/{node_id}/related", response_model=list[NodeResponse])
async def get_related_nodes(
    node_id: str,
    relationship_type: Optional[RelationshipType] = None,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Get nodes related to a given node."""
    service = IdentityService(db)
    nodes = await service.get_related_nodes(user_id, node_id, relationship_type)
    
    return [
        NodeResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type.value,
            name=n.name,
            data=n.data,
            confidence=n.confidence,
        )
        for n in nodes
    ]
