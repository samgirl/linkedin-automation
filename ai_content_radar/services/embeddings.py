"""Embedding generation and similarity computation."""
from __future__ import annotations

import json
import logging
import hashlib
from typing import Optional

import numpy as np

from ai_content_radar.config.settings import config, DATA_DIR
from ai_content_radar.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(config.ai.embedding_model)
            logger.info(f"Loaded embedding model: {config.ai.embedding_model}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Using fallback embeddings.")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _model


def generate_embedding(text: str) -> Optional[list[float]]:
    """Generate an embedding vector for the given text."""
    model = _get_model()
    if model is None:
        return _fallback_embedding(text)

    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return _fallback_embedding(text)


def generate_embeddings_batch(texts: list[str]) -> list[Optional[list[float]]]:
    """Generate embeddings for a batch of texts."""
    model = _get_model()
    if model is None:
        return [_fallback_embedding(t) for t in texts]

    try:
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        return [_fallback_embedding(t) for t in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)

    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def find_similar(
    query_embedding: list[float],
    candidate_embeddings: list[tuple[str, list[float]]],
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """Find the most similar embeddings to the query.

    Args:
        query_embedding: The query vector.
        candidate_embeddings: List of (id, vector) tuples.
        top_k: Number of top results to return.

    Returns:
        List of (id, similarity_score) tuples, sorted by score descending.
    """
    if not candidate_embeddings:
        return []

    scores = []
    for cid, emb in candidate_embeddings:
        sim = cosine_similarity(query_embedding, emb)
        scores.append((cid, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def _fallback_embedding(text: str) -> list[float]:
    """Simple hash-based fallback embedding when sentence-transformers is not available."""
    hash_obj = hashlib.sha512(text.lower().encode())
    hash_bytes = hash_obj.digest()
    vec = []
    for i in range(0, min(len(hash_bytes), 384), 1):
        vec.append((hash_bytes[i] / 255.0) * 2 - 1)

    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


class EmbeddingStore:
    """Manages embedding storage and retrieval using a local file-based store."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._store_path = DATA_DIR / "embeddings.json"
        self._store: dict[str, list[float]] = self._load()

    def _load(self) -> dict[str, list[float]]:
        if self._store_path.exists():
            try:
                with open(self._store_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._store_path, "w") as f:
            json.dump(self._store, f)

    def store(self, key: str, embedding: list[float]) -> None:
        self._store[key] = embedding
        if len(self._store) % 50 == 0:
            self._save()

    def get(self, key: str) -> Optional[list[float]]:
        return self._store.get(key)

    def get_all(self) -> list[tuple[str, list[float]]]:
        return [(k, v) for k, v in self._store.items()]

    def contains(self, key: str) -> bool:
        return key in self._store

    def remove(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> int:
        count = len(self._store)
        self._store = {}
        self._save()
        return count

    def save_to_disk(self) -> None:
        self._save()
