"""Unit tests for embeddings."""
from __future__ import annotations

import unittest

from ai_content_radar.services.embeddings import (
    EmbeddingStore,
    cosine_similarity,
    generate_embedding,
)


class TestEmbeddings(unittest.TestCase):
    """Tests for embedding functions."""

    def test_generate_embedding(self) -> None:
        emb = generate_embedding("Technology transfer in synthetic biology")
        self.assertIsNotNone(emb)
        self.assertIsInstance(emb, list)
        self.assertGreater(len(emb), 0)

    def test_generate_embedding_empty(self) -> None:
        emb = generate_embedding("")
        self.assertIsNotNone(emb)

    def test_cosine_similarity_identical(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(a, b), 1.0, places=5)

    def test_cosine_similarity_orthogonal(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(a, b), 0.0, places=5)

    def test_cosine_similarity_opposite(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(a, b), -1.0, places=5)

    def test_cosine_similarity_zero_vector(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(a, b), 0.0, places=5)


class TestEmbeddingStore(unittest.TestCase):
    """Tests for EmbeddingStore."""

    def setUp(self) -> None:
        from ai_content_radar.database.manager import DatabaseManager
        self.db = DatabaseManager("sqlite:///:memory:")
        self.db.create_tables()
        self.store = EmbeddingStore(self.db)

    def test_store_and_get(self) -> None:
        emb = [0.1, 0.2, 0.3]
        self.store.store("test:1", emb)
        result = self.store.get("test:1")
        self.assertEqual(result, emb)

    def test_get_nonexistent(self) -> None:
        result = self.store.get("nonexistent")
        self.assertIsNone(result)

    def test_contains(self) -> None:
        self.store.store("test:2", [0.1, 0.2])
        self.assertTrue(self.store.contains("test:2"))
        self.assertFalse(self.store.contains("test:3"))

    def test_remove(self) -> None:
        self.store.store("test:3", [0.1, 0.2])
        removed = self.store.remove("test:3")
        self.assertTrue(removed)
        self.assertIsNone(self.store.get("test:3"))

    def test_get_all(self) -> None:
        self.store.store("a:1", [0.1])
        self.store.store("b:1", [0.2])
        all_items = self.store.get_all()
        self.assertEqual(len(all_items), 2)

    def test_clear(self) -> None:
        self.store.store("c:1", [0.1])
        self.store.store("c:2", [0.2])
        count = self.store.clear()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.store.get_all()), 0)


if __name__ == "__main__":
    unittest.main()
