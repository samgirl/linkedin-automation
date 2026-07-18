"""Memory consolidator worker - consolidates related memories."""

from pros.src.workers.base import BaseWorker
from pros.src.db.database import get_session
from pros.src.core.memory.service import MemoryService
from pros.src.ai.orchestrator import get_ai
from sqlalchemy import select
from pros.src.db.models import Memory


class MemoryConsolidatorWorker(BaseWorker):
    """Consolidates related memories and builds connections."""
    
    def __init__(self):
        super().__init__(interval_minutes=30)  # Run every 30 minutes
    
    async def run_once(self):
        """Consolidate related memories."""
        async for session in get_session():
            try:
                memory_service = MemoryService(session)
                ai = get_ai()
                
                # Get memories needing consolidation
                result = await session.execute(
                    select(Memory)
                    .where(Memory.consolidated == False)
                    .order_by(Memory.created_at.desc())
                    .limit(50)
                )
                memories = result.scalars().all()
                
                if len(memories) < 3:
                    return  # Need at least 3 memories to consolidate
                
                # Find clusters of related memories
                clusters = await self._find_clusters(memories, ai)
                
                # Create connections between related memories
                for cluster in clusters:
                    primary = cluster["primary"]
                    related = cluster["related"]
                    relationship = cluster["relationship"]
                    
                    for related_id in related:
                        await memory_service.add_relationship(
                            primary,
                            related_id,
                            relationship,
                            strength=0.8,
                        )
                
                # Mark memories as consolidated
                for memory in memories:
                    memory.consolidated = True
                
                await session.commit()
                
            except Exception as e:
                print(f"Memory consolidation error: {e}")
                await session.rollback()
    
    async def _find_clusters(self, memories: list, ai) -> list[dict]:
        """Find clusters of related memories."""
        # Build memory descriptions
        memory_descriptions = []
        for m in memories:
            desc = f"ID: {m.id}\nType: {m.type}\nContent: {m.content[:200]}"
            memory_descriptions.append(desc)
        
        memories_text = "\n\n".join(memory_descriptions)
        
        prompt = f"""Given these memories, find clusters of related memories.
For each cluster, identify the primary memory and related memories.
Describe the relationship between them.

Memories:
{memories_text[:4000]}

Return JSON array of clusters:
{{
  "primary": "memory_id",
  "related": ["related_id1", "related_id2"],
  "relationship": "description of how they relate"
}}"""
        
        response = await ai.complete(prompt, temperature=0.3, max_tokens=1000)
        
        # Parse JSON
        import json
        import re
        try:
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return []
