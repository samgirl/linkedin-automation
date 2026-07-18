"""Unit tests for learning engine."""
from __future__ import annotations

import unittest

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.learning import LearningEngine
from ai_content_radar.services.ranking import RankingEngine
from ai_content_radar.services.taxonomy import KeywordTaxonomy


class TestLearningEngine(unittest.TestCase):
    """Tests for LearningEngine."""

    def setUp(self) -> None:
        self.db = DatabaseManager("sqlite:///:memory:")
        self.db.create_tables()
        self.taxonomy = KeywordTaxonomy()
        self.learning = LearningEngine(self.db)
        self.ranking = RankingEngine(self.db, self.taxonomy, self.learning)

    def tearDown(self) -> None:
        self.db.drop_tables()

    def _add_post(self, text: str, **kwargs) -> int:
        post = self.db.add_post({
            "url": kwargs.get("url", "https://example.com/test"),
            "text": text,
            "title": kwargs.get("title", ""),
            "hashtags": kwargs.get("hashtags", []),
            "mentioned_tech": kwargs.get("mentioned_tech", []),
        })
        return post.id

    def test_record_action_approved(self) -> None:
        post_id = self._add_post("Technology transfer post")
        stats = self.learning.record_action(post_id, "approved")
        self.assertEqual(stats["total_actions"], 1)
        self.assertEqual(stats["approval_rate"], 1.0)

    def test_record_action_rejected(self) -> None:
        post_id = self._add_post("Marketing tips post")
        stats = self.learning.record_action(post_id, "rejected")
        self.assertEqual(stats["total_actions"], 1)
        self.assertEqual(stats["approval_rate"], 0.0)

    def test_multiple_actions(self) -> None:
        post1 = self._add_post("Approved post", url="https://example.com/a")
        post2 = self._add_post("Rejected post", url="https://example.com/r")
        self.learning.record_action(post1, "approved")
        stats = self.learning.record_action(post2, "rejected")
        self.assertEqual(stats["total_actions"], 2)
        self.assertAlmostEqual(stats["approval_rate"], 0.5)

    def test_keyword_preferences(self) -> None:
        post_id = self._add_post(
            "Synthetic biology is exciting",
            url="https://example.com/kw",
            hashtags=["synbio"],
            mentioned_tech=["synthetic biology"],
        )
        self.learning.record_action(post_id, "approved")
        prefs = self.learning.get_preference_summary()
        self.assertGreater(len(prefs["top_keywords"]), 0)

    def test_personalized_boost(self) -> None:
        post_id = self._add_post(
            "Technology transfer in biotech",
            url="https://example.com/boost",
            mentioned_tech=["technology transfer"],
        )
        self.learning.record_action(post_id, "approved")
        post = self.db.get_post_by_id(post_id)
        boost = self.learning.get_personalized_boost(post)
        self.assertGreater(boost, 0)

    def test_embedding_generation(self) -> None:
        post_id = self._add_post(
            "Embedding test post about deep tech",
            url="https://example.com/embed",
        )
        result = self.learning.embed_post(post_id)
        self.assertTrue(result)
        embedding = self.learning.embedding_store.get(f"post:{post_id}")
        self.assertIsNotNone(embedding)

    def test_similar_posts(self) -> None:
        post1 = self._add_post(
            "Technology transfer and IP commercialization",
            url="https://example.com/sim1",
        )
        post2 = self._add_post(
            "Patent licensing and university spinouts",
            url="https://example.com/sim2",
        )
        self.learning.embed_post(post1)
        self.learning.embed_post(post2)
        similar = self.learning.get_similar_posts(post1)
        self.assertEqual(len(similar), 1)
        self.assertEqual(similar[0][0], post2)

    def test_ranking_with_learning(self) -> None:
        post_id = self._add_post(
            "Synthetic biology advances",
            url="https://example.com/rank_learn",
            mentioned_tech=["synthetic biology"],
        )
        self.learning.record_action(post_id, "approved")
        result = self.ranking.rank_post(post_id)
        self.assertIsNotNone(result)
        self.assertIn("personalization boost", result["reason"])


if __name__ == "__main__":
    unittest.main()
