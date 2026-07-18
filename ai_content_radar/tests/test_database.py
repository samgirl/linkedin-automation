"""Unit tests for database manager."""
from __future__ import annotations

import json
import unittest
from datetime import datetime

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.models.database import Base


class TestDatabaseManager(unittest.TestCase):
    """Tests for DatabaseManager."""

    def setUp(self) -> None:
        self.db = DatabaseManager("sqlite:///:memory:")
        self.db.create_tables()

    def tearDown(self) -> None:
        self.db.drop_tables()

    def test_create_tables(self) -> None:
        self.assertTrue(True)

    def test_add_post(self) -> None:
        post = self.db.add_post({
            "url": "https://example.com/post/1",
            "title": "Test Post",
            "text": "This is test content about technology transfer.",
            "source": "linkedin",
        })
        self.assertIsNotNone(post)
        self.assertEqual(post.url, "https://example.com/post/1")
        self.assertEqual(post.title, "Test Post")

    def test_add_post_duplicate(self) -> None:
        self.db.add_post({"url": "https://example.com/post/1", "text": "First"})
        result = self.db.add_post({"url": "https://example.com/post/1", "text": "Duplicate"})
        self.assertIsNone(result)

    def test_get_post_by_id(self) -> None:
        post = self.db.add_post({"url": "https://example.com/post/2", "text": "Content"})
        fetched = self.db.get_post_by_id(post.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.url, "https://example.com/post/2")

    def test_get_posts(self) -> None:
        for i in range(5):
            self.db.add_post({"url": f"https://example.com/post/{i}", "text": f"Content {i}"})
        posts = self.db.get_posts(limit=3)
        self.assertEqual(len(posts), 3)

    def test_add_keyword(self) -> None:
        kw = self.db.add_keyword("technology transfer", "Technology Transfer", 1.2)
        self.assertIsNotNone(kw)
        self.assertEqual(kw.term, "technology transfer")

    def test_add_keyword_duplicate(self) -> None:
        self.db.add_keyword("tech transfer", "Technology Transfer")
        result = self.db.add_keyword("tech transfer", "Technology Transfer")
        self.assertEqual(result.term, "tech transfer")

    def test_get_keywords(self) -> None:
        self.db.add_keyword("kw1", "Domain A")
        self.db.add_keyword("kw2", "Domain A")
        self.db.add_keyword("kw3", "Domain B")
        all_kw = self.db.get_keywords()
        self.assertEqual(len(all_kw), 3)
        domain_a = self.db.get_keywords(domain="Domain A")
        self.assertEqual(len(domain_a), 2)

    def test_add_ranking(self) -> None:
        post = self.db.add_post({"url": "https://example.com/r1", "text": "Content"})
        ranking = self.db.add_ranking({
            "post_id": post.id,
            "score": 85,
            "reason": "Strong keyword match",
            "keyword_match_score": 90.0,
            "quality_score": 80.0,
        })
        self.assertEqual(ranking.score, 85)

    def test_get_ranked_posts(self) -> None:
        post1 = self.db.add_post({"url": "https://example.com/rp1", "text": "A"})
        post2 = self.db.add_post({"url": "https://example.com/rp2", "text": "B"})
        self.db.add_ranking({"post_id": post1.id, "score": 50})
        self.db.add_ranking({"post_id": post2.id, "score": 90})
        ranked = self.db.get_ranked_posts(min_score=60)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0][1].score, 90)

    def test_add_comment(self) -> None:
        post = self.db.add_post({"url": "https://example.com/c1", "text": "Content"})
        comment = self.db.add_comment({
            "post_id": post.id,
            "comment_type": "professional",
            "text": "This is a professional comment.",
            "word_count": 6,
        })
        self.assertEqual(comment.text, "This is a professional comment.")

    def test_record_action(self) -> None:
        post = self.db.add_post({"url": "https://example.com/a1", "text": "Content"})
        action = self.db.record_action(post.id, "approved")
        self.assertEqual(action.action, "approved")

    def test_get_action_counts(self) -> None:
        post1 = self.db.add_post({"url": "https://example.com/ac1", "text": "A"})
        post2 = self.db.add_post({"url": "https://example.com/ac2", "text": "B"})
        self.db.record_action(post1.id, "approved")
        self.db.record_action(post2.id, "rejected")
        counts = self.db.get_action_counts()
        self.assertEqual(counts["approved"], 1)
        self.assertEqual(counts["rejected"], 1)

    def test_knowledge(self) -> None:
        pk = self.db.add_knowledge("project", "Current Work", "Technology transfer in biotech")
        self.assertEqual(pk.key, "Current Work")
        entries = self.db.get_knowledge(category="project")
        self.assertEqual(len(entries), 1)
        deleted = self.db.delete_knowledge(pk.id)
        self.assertTrue(deleted)
        self.assertEqual(len(self.db.get_knowledge()), 0)

    def test_search_history(self) -> None:
        self.db.add_search_history({"query": "tech transfer", "results_count": 10})
        history = self.db.get_search_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].query, "tech transfer")

    def test_cache(self) -> None:
        self.db.set_cache("key1", '{"data": "test"}', "search")
        result = self.db.get_cache("key1")
        self.assertIsNotNone(result)
        self.assertIn("test", result)

    def test_analytics(self) -> None:
        analytics = self.db.get_analytics()
        self.assertEqual(analytics["total_posts"], 0)
        self.assertEqual(analytics["approved"], 0)


if __name__ == "__main__":
    unittest.main()
