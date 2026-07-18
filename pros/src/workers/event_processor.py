"""Event processor worker - processes incoming events."""

from pros.src.workers.base import BaseWorker
from pros.src.db.database import get_session
from pros.src.db.models import Event
from pros.src.core.memory.service import MemoryService
from pros.src.core.identity.service import IdentityService
from pros.src.ai.orchestrator import get_ai
from sqlalchemy import select


class EventProcessorWorker(BaseWorker):
    """Processes events into memories and identity updates."""
    
    def __init__(self):
        super().__init__(interval_minutes=2)  # Run every 2 minutes
    
    async def run_once(self):
        """Process unprocessed events."""
        async for session in get_session():
            try:
                # Get unprocessed events
                result = await session.execute(
                    select(Event)
                    .where(Event.processed == False)
                    .order_by(Event.created_at)
                    .limit(10)
                )
                events = result.scalars().all()
                
                if not events:
                    return
                
                # Initialize services
                memory_service = MemoryService(session)
                identity_service = IdentityService(session)
                ai = get_ai()
                
                for event in events:
                    await self._process_event(
                        event, memory_service, identity_service, ai
                    )
                    event.processed = True
                
                await session.commit()
                
            except Exception as e:
                print(f"Event processing error: {e}")
                await session.rollback()
    
    async def _process_event(self, event, memory_service, identity_service, ai):
        """Process a single event."""
        # Create memory from event
        memory = await memory_service.create_from_event(
            event.user_id,
            event.id,
            {
                "content": event.content,
                "event_type": event.event_type,
                "source": event.source,
                "raw_data": event.raw_data,
            }
        )
        
        # Extract topics using AI
        topics = await self._extract_topics(event.content, ai)
        if topics:
            await memory_service.update(memory.id, topics=topics)
        
        # Extract entities
        entities = await self._extract_entities(event.content, ai)
        for entity in entities:
            await identity_service.add_node(
                event.user_id,
                entity["name"],
                entity["type"],
                {"extracted_from": event.id},
            )
    
    async def _extract_topics(self, content: str, ai) -> list[str]:
        """Extract topics from content."""
        prompt = f"""Extract 3-5 key topics from this text. Return as JSON array.

Text: {content[:1000]}

Topics (JSON array):"""
        
        response = await ai.complete(prompt, temperature=0.3, max_tokens=200)
        
        # Parse JSON
        import json
        try:
            # Find JSON array in response
            import re
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return []
    
    async def _extract_entities(self, content: str, ai) -> list[dict]:
        """Extract entities from content."""
        prompt = f"""Extract key entities (people, companies, technologies, projects) from this text.
Return as JSON array of objects with "name" and "type" fields.

Text: {content[:1000]}

Entities (JSON array):"""
        
        response = await ai.complete(prompt, temperature=0.3, max_tokens=300)
        
        # Parse JSON
        import json
        try:
            import re
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return []
