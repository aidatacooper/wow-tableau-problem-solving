"""Tests for the read-only case intake helper."""

import unittest
from unittest.mock import patch

from scripts import case_intake


class CaseIntakeTests(unittest.TestCase):
    def test_slug_normalizes_punctuation_and_whitespace(self):
        self.assertEqual(
            case_intake._slug("Can you format your numbers to the right scale?"),
            "can-you-format-your-numbers-to-the-right-scale",
        )
        self.assertEqual(case_intake._slug("  Mixed   CASE -- 42  "), "mixed-case-42")

    def test_find_article_accepts_url_and_filename(self):
        by_url = case_intake.find_article(
            "https://donnacoles.home.blog/2026/04/13/can-you-calculate-the-correct-metric/"
        )
        by_file = case_intake.find_article(
            "posts/2026-04-13-Can_you_calculate_the_correct_metric.html"
        )
        self.assertEqual(by_url["file"], by_file["file"])
        self.assertEqual(by_url["date"], "2026-04-13")

    def test_find_article_tolerates_missing_trailing_slash(self):
        with_slash = case_intake.find_article(
            "https://donnacoles.home.blog/2026/04/13/can-you-calculate-the-correct-metric/"
        )
        without = case_intake.find_article(
            "https://donnacoles.home.blog/2026/04/13/can-you-calculate-the-correct-metric"
        )
        self.assertEqual(with_slash["file"], without["file"])

    def test_find_article_rejects_unknown_reference(self):
        with self.assertRaises(SystemExit):
            case_intake.find_article("https://example.com/not-a-post/")

    def test_find_workbook_returns_tableau_public_link(self):
        article = case_intake.find_article(
            "posts/2026-04-13-Can_you_calculate_the_correct_metric.html"
        )
        workbook = case_intake.find_workbook(article["file"])
        self.assertIsNotNone(workbook)
        self.assertEqual(workbook["workbook"], "2026_04_08_WW14_Weighted_Avg")
        self.assertTrue(workbook["viz_url"].startswith("https://public.tableau.com/views/"))

    def test_resolve_challenge_prefers_slug_and_handles_network_failure(self):
        """A failed lookup must degrade to an empty result, never raise."""
        with patch.object(case_intake, "_wp_get", return_value=[]):
            resolved = case_intake.resolve_challenge("Some title", 2026, 14)
        self.assertEqual(resolved["candidates"], [])

    def test_resolve_challenge_orders_slug_hit_first(self):
        slug_post = {
            "id": 1,
            "date": "2026-04-08T09:13:48",
            "title": {"rendered": "#WOW2026 | Week 14 | Exact"},
            "link": "https://www.workout-wednesday.com/2026w14tab/",
        }
        search_post = {
            "id": 2,
            "date": "2020-01-01T00:00:00",
            "title": {"rendered": "Unrelated"},
            "link": "https://www.workout-wednesday.com/unrelated/",
        }

        def fake_get(params):
            return [slug_post] if "slug" in params else [search_post]

        with patch.object(case_intake, "_wp_get", side_effect=fake_get):
            resolved = case_intake.resolve_challenge("Some title", 2026, 14)
        self.assertEqual(resolved["candidates"][0]["id"], 1)
        self.assertEqual(resolved["candidates"][0]["date"], "2026-04-08")


if __name__ == "__main__":
    unittest.main()
