"""A visual claim must be backed by a committed visual artifact.

Regression for the gap that let a case assert ``visual_status:
acceptable_delta`` with no rendered image behind it: the workbook opened in
Desktop but rendered empty, and every existing check still passed.
"""

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import validate_iteration as validation


def make_case(root: Path, *, visual_status="acceptable_delta", verification_status="verified",
              cloud_author="outputs/cloud-author.png", cloud_replica="outputs/cloud-replica.png",
              write_images=True):
    case = root / "iterations" / "2026-01-01-ww01-example"
    (case / "outputs").mkdir(parents=True)
    (case / "inputs").mkdir(parents=True)
    (case / "analysis.md").write_text("# analysis\n", encoding="utf-8")
    (case / "build_replication.py").write_text("# builder\n", encoding="utf-8")
    (case / "verify_replication.py").write_text("# acceptance: example\n", encoding="utf-8")
    (case / "inputs/source-lock.json").write_text("{}\n", encoding="utf-8")
    (case / "outputs/replicated-workbook.twbx").write_bytes(b"workbook")
    if write_images:
        for name in (cloud_author, cloud_replica):
            if name:
                (case / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    metadata = {
        "schema_version": "1.1.0",
        "case_id": "wow-2026-ww01-example",
        "iteration_id": "2026-01-01-ww01-example",
        "post": "posts/example.html",
        "legacy_case_ids": {},
        "article_date": "2026-01-01",
        "challenge_year": 2026,
        "challenge_week": 1,
        "challenge_date": None,
        "date_evidence": {},
        "source": {"challenge": {"url": "https://example.com"}, "article": {}, "workbook": {}},
        "verification_status": verification_status,
        "artifacts": {
            "primary_workbook": "outputs/replicated-workbook.twbx",
            "cloud_author": cloud_author,
            "cloud_replica": cloud_replica,
        },
        "artifact_aliases": {},
        "historical_artifacts": [],
        "evidence": ["inputs/source-lock.json"],
        "notes": [],
        "cwtwb": {"tested_version": "0.27.1", "runs": [{"version": "0.27.1", "result": "pass", "evidence": "verify_replication.py"}]},
        "analysis_status": "completed",
        "functional_status": "replicated",
        "visual_status": visual_status,
        "cwtwb_result": "pass",
        "inputs": {"source_lock": "inputs/source-lock.json", "data_files": []},
        "acceptance": [{"id": "example", "description": "Observable.", "mode": "automated"}],
    }
    (case / "case.yaml").write_text(yaml.safe_dump(metadata, allow_unicode=True), encoding="utf-8")
    return case


class VisualEvidenceTests(unittest.TestCase):
    def test_visual_claim_without_images_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            case = make_case(Path(directory), cloud_author=None, cloud_replica=None, write_images=False)
            with self.assertRaisesRegex(AssertionError, "requires artifacts.cloud_author"):
                validation.validate_metadata(case)

    def test_visual_claim_pointing_at_missing_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            case = make_case(Path(directory), write_images=False)
            with self.assertRaisesRegex(AssertionError, "does not exist"):
                validation.validate_metadata(case)

    def test_not_evaluated_needs_no_images(self):
        with tempfile.TemporaryDirectory() as directory:
            case = make_case(Path(directory), visual_status="not_evaluated",
                             cloud_author=None, cloud_replica=None, write_images=False)
            metadata = validation.validate_metadata(case)
            self.assertEqual(metadata["visual_status"], "not_evaluated")

    def test_historical_case_is_grandfathered(self):
        with tempfile.TemporaryDirectory() as directory:
            case = make_case(Path(directory), verification_status="historical",
                             cloud_author=None, cloud_replica=None, write_images=False)
            metadata = validation.validate_metadata(case)
            self.assertEqual(metadata["verification_status"], "historical")

    def test_visual_claim_with_images_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            case = make_case(Path(directory))
            metadata = validation.validate_metadata(case)
            self.assertEqual(metadata["visual_status"], "acceptable_delta")


if __name__ == "__main__":
    unittest.main()
