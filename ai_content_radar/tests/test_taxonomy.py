"""Unit tests for keyword taxonomy."""
from __future__ import annotations

import json
import unittest

from ai_content_radar.services.taxonomy import KeywordTaxonomy


class TestKeywordTaxonomy(unittest.TestCase):
    """Tests for KeywordTaxonomy."""

    def setUp(self) -> None:
        self.taxonomy = KeywordTaxonomy()

    def test_domains_exist(self) -> None:
        self.assertGreater(len(self.taxonomy.domains), 0)

    def test_keyword_count(self) -> None:
        self.assertGreater(self.taxonomy.total_keywords(), 100)

    def test_get_domain_keywords(self) -> None:
        kw = self.taxonomy.get_domain_keywords("Technology Transfer")
        self.assertGreater(len(kw), 0)
        self.assertIsInstance(kw[0], dict)
        self.assertIn("term", kw[0])

    def test_get_all_keywords_flat(self) -> None:
        flat = self.taxonomy.get_all_keywords_flat()
        self.assertEqual(len(flat), self.taxonomy.total_keywords())
        for kw in flat:
            self.assertIn("domain", kw)
            self.assertIn("term", kw)

    def test_add_keyword(self) -> None:
        initial_count = self.taxonomy.total_keywords()
        self.taxonomy.add_keyword("Unique Test Domain XYZ", "unique test keyword 789", 1.5)
        self.assertEqual(self.taxonomy.total_keywords(), initial_count + 1)

    def test_add_keyword_update(self) -> None:
        self.taxonomy.add_keyword("Test Domain", "updateable", 1.0)
        self.taxonomy.add_keyword("Test Domain", "updateable", 2.0)
        kw = self.taxonomy.get_domain_keywords("Test Domain")
        updateable = [k for k in kw if k["term"] == "updateable"]
        self.assertEqual(len(updateable), 1)
        self.assertEqual(updateable[0]["weight"], 2.0)

    def test_remove_keyword(self) -> None:
        self.taxonomy.add_keyword("Test Domain", "removable")
        removed = self.taxonomy.remove_keyword("Test Domain", "removable")
        self.assertTrue(removed)

    def test_search(self) -> None:
        results = self.taxonomy.search("technology")
        self.assertGreater(len(results), 0)

    def test_search_by_alias(self) -> None:
        results = self.taxonomy.search("tech transfer")
        self.assertGreater(len(results), 0)

    def test_get_search_terms(self) -> None:
        terms = self.taxonomy.get_search_terms(["Technology Transfer"])
        self.assertGreater(len(terms), 0)
        self.assertIsInstance(terms[0], str)

    def test_persistence(self) -> None:
        self.taxonomy.add_keyword("Persist Domain", "persist me")
        new_taxonomy = KeywordTaxonomy()
        found = new_taxonomy.search("persist me")
        self.assertGreater(len(found), 0)


if __name__ == "__main__":
    unittest.main()
