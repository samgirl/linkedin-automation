"""Unit tests for export service."""
from __future__ import annotations

import json
import unittest

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.export import ExportService


class TestExportService(unittest.TestCase):
    """Tests for ExportService."""

    def setUp(self) -> None:
        self.db = DatabaseManager("sqlite:///:memory:")
        self.db.create_tables()
        self.exporter = ExportService(self.db)

    def tearDown(self) -> None:
        self.db.drop_tables()

    def _add_sample_data(self) -> None:
        post = self.db.add_post({
            "url": "https://example.com/export/1",
            "title": "Export Test Post",
            "text": "Technology transfer content",
            "source": "linkedin",
        })
        self.db.add_ranking({"post_id": post.id, "score": 85, "reason": "Strong match"})
        self.db.add_comment({
            "post_id": post.id,
            "comment_type": "professional",
            "text": "Great perspective on tech transfer.",
            "word_count": 6,
        })
        self.db.record_action(post.id, "approved")
        self.db.add_search_history({"query": "tech transfer", "results_count": 10})
        self.db.add_knowledge("project", "Work", "Tech transfer")

    def test_export_approved_json(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_approved_comments("json")
        data = json.loads(result)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["url"], "https://example.com/export/1")

    def test_export_posts_csv(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_all_posts("csv")
        self.assertIn("url", result)
        self.assertIn("Export Test Post", result)

    def export_rankings_markdown(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_rankings("markdown")
        self.assertIn("rankings", result.lower())

    def test_export_search_history(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_search_history("json")
        data = json.loads(result)
        self.assertEqual(len(data), 1)

    def test_export_knowledge_base(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_knowledge_base("json")
        data = json.loads(result)
        self.assertEqual(len(data), 1)

    def test_export_analytics(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_analytics("json")
        data = json.loads(result)
        self.assertIn("total_posts", data[0])

    def test_export_all(self) -> None:
        self._add_sample_data()
        result = self.exporter.export_all("json")
        data = json.loads(result)
        self.assertIn("exported_at", data)
        self.assertIn("rankings", data)

    def test_empty_export(self) -> None:
        result = self.exporter.export_approved_comments("json")
        data = json.loads(result)
        self.assertEqual(len(data), 0)


if __name__ == "__main__":
    unittest.main()
