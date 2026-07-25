"""
VectorStore — works with or without ChromaDB.
- With ChromaDB: full semantic search
- Without: falls back to PostgreSQL text search (trigram/ILIKE)
"""
import logging

logger = logging.getLogger(__name__)

_collection_name = "pros_memories"


class VectorStore:
    def __init__(self):
        self._client = None
        self._mode = None  # 'chroma' | 'pg' | None

    def _get_mode(self):
        if self._mode is not None:
            return self._mode

        from app.config import get_settings
        settings = get_settings()

        # Try ChromaDB if configured
        if settings.chroma_host and settings.chroma_host not in ('localhost', ''):
            try:
                import chromadb
                self._client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                )
                self._client.heartbeat()
                self._mode = 'chroma'
                logger.info("Using ChromaDB for vector search")
                return self._mode
            except Exception as e:
                logger.warning(f"ChromaDB unavailable ({e}), falling back to PostgreSQL")

        # Fall back to PostgreSQL text search
        self._mode = 'pg'
        logger.info("Using PostgreSQL text search (no vector embeddings)")
        return self._mode

    def _get_collection(self, user_id: str):
        client = self._client
        return client.get_or_create_collection(
            name=f"{_collection_name}_{user_id}",
            metadata={"hnsw:space": "cosine"},
        )

    async def store_memory(self, user_id: str, memory_id: str, content: str, metadata: dict = None) -> str:
        mode = self._get_mode()

        if mode == 'chroma':
            try:
                collection = self._get_collection(user_id)
                meta = metadata or {}
                meta["memory_id"] = memory_id
                collection.upsert(
                    ids=[memory_id],
                    documents=[content],
                    metadatas=[meta],
                )
                return memory_id
            except Exception as e:
                logger.warning(f"ChromaDB store failed: {e}")

        # PG mode: just return the memory_id — content is already in PostgreSQL
        return memory_id

    async def search(self, user_id: str, query: str, n_results: int = 10) -> list:
        mode = self._get_mode()

        if mode == 'chroma':
            try:
                collection = self._get_collection(user_id)
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=["documents", "distances", "metadatas"],
                )
                # Flatten results
                docs = results.get("documents", [[]])[0]
                return docs
            except Exception as e:
                logger.warning(f"ChromaDB search failed: {e}")

        # PG fallback: use PostgreSQL ILIKE for text matching
        try:
            from app.database import async_session
            from app.models.context import Memory
            from sqlalchemy import select, or_

            async with async_session() as session:
                # Simple text search across memories
                terms = [t.strip() for t in query.split() if len(t.strip()) > 2][:5]
                conditions = [Memory.content.ilike(f"%{term}%") for term in terms]

                result = await session.execute(
                    select(Memory)
                    .where(Memory.user_id == user_id, Memory.archived == False)
                    .where(or_(*conditions) if conditions else Memory.content.ilike("%%"))
                    .order_by(Memory.importance.desc())
                    .limit(n_results)
                )
                memories = result.scalars().all()
                return [m.content[:500] for m in memories]
        except Exception as e:
            logger.warning(f"PG search failed: {e}")
            return []

    async def delete_memory(self, user_id: str, memory_id: str):
        mode = self._get_mode()
        if mode == 'chroma':
            try:
                collection = self._get_collection(user_id)
                collection.delete(ids=[memory_id])
            except Exception:
                pass
