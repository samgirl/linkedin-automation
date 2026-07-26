import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.context import Event, Memory, Identity
from app.models.journal import JournalEntry, SavedContent


class ContextEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_event(self, user_id: str, event_type: str, source: str,
                           title: str = None, content: str = None, metadata: dict = None) -> Event:
        event = Event(
            user_id=user_id,
            type=event_type,
            source=source,
            title=title,
            content=content,
            extra_data=metadata or {},
        )
        self.db.add(event)
        await self.db.flush()

        memory = await self._create_memory_from_event(user_id, event)
        if memory:
            try:
                from app.services.vector_store import VectorStore
                vs = VectorStore()
                embedding_id = await vs.store_memory(user_id, memory.id, memory.content, {"type": memory.type})
                memory.embedding_id = embedding_id
                await self.db.flush()
            except Exception:
                pass  # Vector store is optional

        await self._update_identity(user_id, event)

        return event

    async def ingest_batch(self, user_id: str, events: list[dict]) -> list[Event]:
        created = []
        for e in events:
            event = await self.ingest_event(
                user_id=user_id,
                event_type=e.get("type", "unknown"),
                source=e.get("source", "unknown"),
                title=e.get("title"),
                content=e.get("content"),
                metadata=e.get("metadata", {}),
            )
            created.append(event)
        return created

    async def ingest_from_journal(self, entry: JournalEntry):
        await self.ingest_event(
            user_id=entry.user_id,
            event_type="journal_entry",
            source="journal",
            title=f"Journal: {entry.entry_type}",
            content=entry.content,
            metadata={"entry_type": entry.entry_type, "tags": entry.tags, "source_url": entry.source_url},
        )

    async def ingest_saved_content(self, item: SavedContent):
        content_text = f"{item.title or ''}\n{item.excerpt or ''}\n{item.notes or ''}".strip()
        await self.ingest_event(
            user_id=item.user_id,
            event_type="saved_content",
            source="extension",
            title=item.title,
            content=content_text,
            metadata={"url": item.url, "tags": item.tags},
        )

    async def import_chatgpt_export(self, data: str, user_id: str) -> list[Event]:
        import json
        try:
            conversations = json.loads(data)
        except json.JSONDecodeError:
            conversations = [{"messages": [{"content": data}]}]

        events = []
        for conv in conversations:
            messages = conv.get("messages", [])
            for msg in messages[-20:]:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    event = await self.ingest_event(
                        user_id=user_id,
                        event_type="chatgpt_conversation",
                        source="chatgpt",
                        title=f"ChatGPT ({msg['role']})",
                        content=msg["content"][:5000],
                        metadata={"role": msg.get("role"), "conversation_id": conv.get("id")},
                    )
                    events.append(event)
        return events

    async def import_claude_export(self, data: str, user_id: str) -> list[Event]:
        import json
        try:
            conversations = json.loads(data)
        except json.JSONDecodeError:
            conversations = [{"messages": [{"content": data}]}]

        events = []
        for conv in conversations:
            messages = conv.get("messages", [])
            for msg in messages[-20:]:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    text = msg["content"]
                    if isinstance(text, list):
                        text = " ".join(b.get("text", "") for b in text if isinstance(b, dict))
                    event = await self.ingest_event(
                        user_id=user_id,
                        event_type="claude_conversation",
                        source="claude",
                        title=f"Claude ({msg['role']})",
                        content=text[:5000],
                        metadata={"role": msg.get("role")},
                    )
                    events.append(event)
        return events

    async def _create_memory_from_event(self, user_id: str, event: Event) -> Memory | None:
        if not event.content or len(event.content.strip()) < 10:
            return None

        memory_type = "fact"
        if event.type in ("chatgpt_conversation", "claude_conversation"):
            memory_type = "preference"
        elif event.type == "journal_entry":
            memory_type = "project"
        elif event.type == "saved_content":
            memory_type = "learning"
        elif event.type in ("linkedin_post", "linkedin_comment"):
            memory_type = "professional"

        content = event.content[:2000]
        memory = Memory(
            user_id=user_id,
            type=memory_type,
            content=content,
            source=event.source,
            source_event_id=event.id,
            tags=event.extra_data.get("tags", []) if isinstance(event.extra_data, dict) else [],
        )
        self.db.add(memory)
        await self.db.flush()
        return memory

    async def _update_identity(self, user_id: str, event: Event):
        """Update user identity model based on accumulated events."""
        # Check if identity entry exists for this event type
        result = await self.db.execute(
            select(Identity).where(
                Identity.user_id == user_id,
                Identity.type == event.type,
            )
        )
        identity = result.scalar_one_or_none()

        if identity:
            # Update confidence and data
            identity.confidence = min(1.0, identity.confidence + 0.05)
            identity.data = {**identity.data, "last_event": event.title} if isinstance(identity.data, dict) else {"last_event": event.title}
        else:
            identity = Identity(
                user_id=user_id,
                type=event.type,
                name=event.title or event.type,
                data={"source": event.source, "count": 1},
                confidence=0.3,
            )
            self.db.add(identity)
        await self.db.flush()

    async def get_identity_summary(self, user_id: str) -> str:
        """Get a text summary of user identity for prompts."""
        result = await self.db.execute(
            select(Identity).where(Identity.user_id == user_id).order_by(Identity.confidence.desc()).limit(20)
        )
        identities = result.scalars().all()
        if not identities:
            return "User identity not yet established."
        lines = [f"- {i.type}: {i.name} (confidence: {i.confidence:.0%})" for i in identities]
        return "\n".join(lines)

    async def get_interests(self, user_id: str) -> dict:
        """Get user interests from identity and memories."""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.archived == False,
            ).order_by(Memory.importance.desc()).limit(20)
        )
        memories = result.scalars().all()

        # Extract interests from tags and content
        all_tags = []
        for m in memories:
            if m.tags:
                all_tags.extend(m.tags)

        tag_freq = {}
        for t in all_tags:
            tag_freq[t] = tag_freq.get(t, 0) + 1

        top_tags = sorted(tag_freq.keys(), key=lambda x: tag_freq[x], reverse=True)[:10]

        return {
            "primary_topics": ", ".join(top_tags) if top_tags else "technology, business, startups",
            "all_tags": tag_freq,
        }

    async def get_recent_memories(self, user_id: str, limit: int = 10) -> list:
        """Get recent memories as text for prompts."""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.archived == False,
            ).order_by(Memory.created_at.desc()).limit(limit)
        )
        memories = result.scalars().all()
        return [{"type": m.type, "content": m.content[:300]} for m in memories]

    async def get_user_context_for_generation(self, user_id: str) -> dict:
        mem_result = await self.db.execute(
            select(Memory).where(Memory.user_id == user_id, Memory.archived == False).order_by(Memory.importance.desc()).limit(50)
        )
        memories = mem_result.scalars().all()

        id_result = await self.db.execute(
            select(Identity).where(Identity.user_id == user_id).order_by(Identity.confidence.desc()).limit(20)
        )
        identities = id_result.scalars().all()

        return {
            "memories": [{"type": m.type, "content": m.content, "importance": m.importance} for m in memories],
            "identity": [{"type": n.type, "name": n.name, "data": n.data} for n in identities],
        }
