"""Unit tests for ranking engine."""
from __future__ import annotations

import unittest

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.ranking import RankingEngine
from ai_content_radar.services.taxonomy import KeywordTaxonomy


class TestRankingEngine(unittest.TestCase):
    """Tests for RankingEngine."""

    def setUp(self) -> None:
        self.db = DatabaseManager("sqlite:///:memory:")
        self.db.create_tables()
        self.taxonomy = KeywordTaxonomy()
        self.engine = RankingEngine(self.db, self.taxonomy)

    def tearDown(self) -> None:
        self.db.drop_tables()

    def _add_post(self, url: str, text: str, **kwargs) -> int:
        post = self.db.add_post({
            "url": url,
            "text": text,
            "title": kwargs.get("title", ""),
            "hashtags": kwargs.get("hashtags", []),
            "mentioned_tech": kwargs.get("mentioned_tech", []),
            "engagement_likes": kwargs.get("likes", 0),
            "engagement_comments": kwargs.get("comments", 0),
            "engagement_shares": kwargs.get("shares", 0),
        })
        return post.id

    def test_rank_post(self) -> None:
        post_id = self._add_post(
            "https://example.com/1",
            "Technology transfer in synthetic biology is advancing rapidly. Precision fermentation shows great promise.",
            hashtags=["biotech", "synbio"],
            mentioned_tech=["synthetic biology", "precision fermentation"],
        )
        result = self.engine.rank_post(post_id)
        self.assertIsNotNone(result)
        self.assertIn("score", result)
        self.assertIn("reason", result)
        self.assertGreater(result["score"], 0)

    def test_rank_post_nonexistent(self) -> None:
        result = self.engine.rank_post(99999)
        self.assertIsNone(result)

    def test_rank_all_unranked(self) -> None:
        self._add_post("https://example.com/r1", "Technology transfer post")
        self._add_post("https://example.com/r2", "Marketing tips post")
        results = self.engine.rank_all_unranked()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["score"] >= results[1]["score"], True)

    def test_keyword_match_score(self) -> None:
        high_match = self._add_post(
            "https://example.com/hm",
            "Technology transfer and IP commercialization in synthetic biology. Deep tech startups.",
            mentioned_tech=["technology transfer", "synthetic biology"],
        )
        low_match = self._add_post(
            "https://example.com/lm",
            "Beautiful sunset today. Nature is wonderful.",
        )
        result_high = self.engine.rank_post(high_match)
        result_low = self.engine.rank_post(low_match)
        self.assertGreater(result_high["keyword_match_score"], result_low["keyword_match_score"])

    def test_quality_score(self) -> None:
        long_post = self._add_post(
            "https://example.com/long",
            "This is a very detailed post about technology transfer. " * 20,
        )
        short_post = self._add_post(
            "https://example.com/short",
            "Short.",
        )
        result_long = self.engine.rank_post(long_post)
        result_short = self.engine.rank_post(short_post)
        self.assertGreater(result_long["quality_score"], result_short["quality_score"])

    def test_opportunity_score(self) -> None:
        question_post = self._add_post(
            "https://example.com/q",
            "Technology transfer: Any suggestions for licensing university patents? What do you think about the process?",
        )
        statement_post = self._add_post(
            "https://example.com/s",
            "Technology transfer is important for the economy.",
        )
        result_q = self.engine.rank_post(question_post)
        result_s = self.engine.rank_post(statement_post)
        self.assertGreater(result_q["opportunity_score"], result_s["opportunity_score"])

    def test_get_ranked_posts(self) -> None:
        post_id = self._add_post("https://example.com/gr", "Test post")
        self.engine.rank_post(post_id)
        ranked = self.engine.get_ranked_posts(min_score=0)
        self.assertEqual(len(ranked), 1)


if __name__ == "__main__":
    unittest.main()
