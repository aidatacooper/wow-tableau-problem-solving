import tempfile
import unittest
from pathlib import Path

import crawler
import download_all


class IncrementalCrawlerTests(unittest.TestCase):
    def test_manifest_deduplicates_by_canonical_url_and_preserves_old_posts(self):
        existing = [
            {"title": "Old title", "date": "2024-01-01", "link": "https://example.test/a", "file": "a.html"},
            {"title": "Archive", "date": "2023-01-01", "link": "https://example.test/b", "file": "b.html"},
        ]
        discovered = [
            {"title": "New title", "date": "2024-01-01", "link": "https://example.test/a", "file": "a.html"},
        ]

        merged = crawler.merge_manifest(discovered, existing)

        self.assertEqual(2, len(merged))
        self.assertEqual("New title", next(item for item in merged if item["link"].endswith("/a"))["title"])
        self.assertTrue(any(item["link"].endswith("/b") for item in merged))

    def test_existing_workbook_is_incomplete_when_a_new_view_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            workbook_dir = Path(directory, "Book")
            workbook_dir.mkdir()
            Path(workbook_dir, "Book.twbx").write_bytes(b"workbook")
            Path(workbook_dir, "ViewA.png").write_bytes(b"image")

            self.assertTrue(download_all.workbook_complete("Book", {"ViewA"}, directory))
            self.assertFalse(download_all.workbook_complete("Book", {"ViewA", "ViewB"}, directory))


if __name__ == "__main__":
    unittest.main()
