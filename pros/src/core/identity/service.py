"""Identity service."""

from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from pros.src.db.models import IdentityNode as NodeModel, IdentityEdge as EdgeModel
from pros.src.core.identity.models import (
    IdentityNode,
    IdentityNodeCreate,
    IdentityEdge,
    IdentityEdgeCreate,
    Identity,
    NodeType,
    RelationshipType,
)
from pros.src.utils import generate_id, utcnow


class IdentityService:
    """Identity service for managing the user's professional identity graph."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # Node operations
    
    async def create_node(self, user_id: str, data: IdentityNodeCreate) -> IdentityNode:
        """Create a new identity node."""
        node = NodeModel(
            id=generate_id(),
            user_id=user_id,
            type=data.type.value,
            name=data.name,
            data=data.data,
            confidence=data.confidence,
            metadata_=data.metadata,
        )
        
        self.session.add(node)
        await self.session.flush()
        
        return IdentityNode.model_validate(node)
    
    async def get_node(self, node_id: str) -> Optional[IdentityNode]:
        """Get a node by ID."""
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.id == node_id)
        )
        node = result.scalar_one_or_none()
        return IdentityNode.model_validate(node) if node else None
    
    async def find_node(
        self,
        user_id: str,
        node_type: NodeType,
        name: str,
    ) -> Optional[IdentityNode]:
        """Find a node by type and name."""
        result = await self.session.execute(
            select(NodeModel).where(
                NodeModel.user_id == user_id,
                NodeModel.type == node_type.value,
                NodeModel.name == name,
            )
        )
        node = result.scalar_one_or_none()
        return IdentityNode.model_validate(node) if node else None
    
    async def get_or_create_node(
        self,
        user_id: str,
        node_type: NodeType,
        name: str,
        data: Optional[dict] = None,
        confidence: float = 0.5,
    ) -> IdentityNode:
        """Get an existing node or create a new one."""
        existing = await self.find_node(user_id, node_type, name)
        
        if existing:
            return existing
        
        return await self.create_node(
            user_id,
            IdentityNodeCreate(
                type=node_type,
                name=name,
                data=data or {},
                confidence=confidence,
            ),
        )
    
    async def list_nodes(
        self,
        user_id: str,
        node_type: Optional[NodeType] = None,
        limit: int = 100,
    ) -> list[IdentityNode]:
        """List nodes for a user."""
        query = select(NodeModel).where(NodeModel.user_id == user_id)
        
        if node_type:
            query = query.where(NodeModel.type == node_type.value)
        
        query = query.order_by(NodeModel.confidence.desc()).limit(limit)
        
        result = await self.session.execute(query)
        nodes = result.scalars().all()
        
        return [IdentityNode.model_validate(n) for n in nodes]
    
    async def update_node(
        self,
        node_id: str,
        data: Optional[dict] = None,
        confidence_delta: float = 0.0,
    ) -> Optional[IdentityNode]:
        """Update a node."""
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return None
        
        if data:
            node.data = {**node.data, **data}
        
        if confidence_delta != 0:
            node.confidence = max(0.0, min(1.0, node.confidence + confidence_delta))
        
        node.updated_at = utcnow()
        
        return IdentityNode.model_validate(node)
    
    # Edge operations
    
    async def create_edge(self, user_id: str, data: IdentityEdgeCreate) -> IdentityEdge:
        """Create a new identity edge."""
        # Check if edge already exists
        result = await self.session.execute(
            select(EdgeModel).where(
                EdgeModel.user_id == user_id,
                EdgeModel.source_id == data.source_id,
                EdgeModel.target_id == data.target_id,
                EdgeModel.relationship_type == data.relationship_type.value,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update strength if edge exists
            existing.strength = max(existing.strength, data.strength)
            return IdentityEdge.model_validate(existing)
        
        edge = EdgeModel(
            id=generate_id(),
            user_id=user_id,
            source_id=data.source_id,
            target_id=data.target_id,
            relationship_type=data.relationship_type.value,
            strength=data.strength,
            metadata_=data.metadata,
        )
        
        self.session.add(edge)
        await self.session.flush()
        
        return IdentityEdge.model_validate(edge)
    
    async def get_edges(
        self,
        user_id: str,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[RelationshipType] = None,
    ) -> list[IdentityEdge]:
        """Get edges with optional filters."""
        query = select(EdgeModel).where(EdgeModel.user_id == user_id)
        
        if source_id:
            query = query.where(EdgeModel.source_id == source_id)
        if target_id:
            query = query.where(EdgeModel.target_id == target_id)
        if relationship_type:
            query = query.where(EdgeModel.relationship_type == relationship_type.value)
        
        result = await self.session.execute(query)
        edges = result.scalars().all()
        
        return [IdentityEdge.model_validate(e) for e in edges]
    
    # Graph operations
    
    async def get_identity(self, user_id: str) -> Identity:
        """Get complete identity snapshot."""
        nodes = await self.list_nodes(user_id, limit=1000)
        edges = await self.get_edges(user_id)
        
        return Identity(nodes=nodes, edges=edges)
    
    async def get_related_nodes(
        self,
        user_id: str,
        node_id: str,
        relationship_type: Optional[RelationshipType] = None,
    ) -> list[IdentityNode]:
        """Get nodes related to a given node."""
        # Get outgoing edges
        outgoing = await self.get_edges(
            user_id,
            source_id=node_id,
            relationship_type=relationship_type,
        )
        
        # Get incoming edges
        incoming = await self.get_edges(
            user_id,
            target_id=node_id,
            relationship_type=relationship_type,
        )
        
        # Collect related node IDs
        related_ids = set()
        for edge in outgoing:
            related_ids.add(edge.target_id)
        for edge in incoming:
            related_ids.add(edge.source_id)
        
        if not related_ids:
            return []
        
        # Fetch nodes
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.id.in_(related_ids))
        )
        nodes = result.scalars().all()
        
        return [IdentityNode.model_validate(n) for n in nodes]
    
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges."""
        # Delete edges first
        await self.session.execute(
            delete(EdgeModel).where(
                (EdgeModel.source_id == node_id) | (EdgeModel.target_id == node_id)
            )
        )
        
        # Delete node
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if node:
            await self.session.delete(node)
            return True
        
        return False
