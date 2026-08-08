import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "build_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_dataset", MODULE_PATH)
build_dataset = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_dataset)


class DatasetBuilderTests(unittest.TestCase):
    def test_consumed_pilot_cases_are_excluded_from_future_selection(self):
        registry_path = (
            Path(__file__).resolve().parents[1]
            / "usage"
            / "consumed-cases.json"
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        selected = [
            {"case_id": "donna-2026-02-02-5ebab8421caf"},
            {"case_id": "donna-2026-02-09-1eb979fd64b6"},
            {"case_id": "donna-2026-02-15-44019b20eed6"},
            {"case_id": "donna-2026-02-22-newcandidate000"},
        ]

        eligible = build_dataset.eligible_cases(selected, registry)

        self.assertEqual(
            eligible,
            [{"case_id": "donna-2026-02-22-newcandidate000"}],
        )
        consumed = build_dataset.consumed_case_ids(registry)
        self.assertTrue({item["case_id"] for item in selected[:3]} <= consumed)
        statuses = {
            item["case_id"]: item["replication_status"]
            for item in registry["consumed_cases"]
        }
        self.assertEqual(statuses["donna-2026-02-02-5ebab8421caf"], "replicated")
        self.assertEqual(statuses["donna-2026-02-09-1eb979fd64b6"], "replicated")
        self.assertEqual(statuses["donna-2026-02-15-44019b20eed6"], "replicated")

    def test_case_id_is_stable_and_date_scoped(self):
        url = "https://donnacoles.home.blog/2026/02/15/example/"
        actual = build_dataset.stable_case_id(url, "2026-02-15")
        expected_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        self.assertEqual(actual, f"donna-2026-02-15-{expected_hash}")

    def test_link_roles_are_conservative(self):
        role, confidence, _ = build_dataset.classify_link(
            "https://public.tableau.com/app/profile/donna.coles/viz/WB/View"
        )
        self.assertEqual(role, "candidate_author_solution")
        self.assertGreaterEqual(confidence, 0.8)

    def test_resources_and_images_are_extracted(self):
        source = """
        <a href="https://www.workout-wednesday.com/challenge">challenge</a>
        <a href="https://example.com/data.xlsx">data</a>
        <img src="https://example.com/image.png" alt="Expected dashboard">
        """
        resources = build_dataset.extract_resources(source)
        self.assertEqual(resources[0]["type"], "challenge")
        self.assertEqual(resources[1]["type"], "downloadable_attachment")
        images = build_dataset.extract_embedded_images(source)
        self.assertEqual(images[0]["alt"], "Expected dashboard")
        self.assertEqual(images[0]["download_status"], "not_collected")

        role, confidence, _ = build_dataset.classify_link(
            "https://public.tableau.com/app/profile/someone.else/viz/WB/View"
        )
        self.assertEqual(role, "external_reference")
        self.assertGreaterEqual(confidence, 0.8)

    def test_valid_twbx_is_extracted_and_described(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            twbx = root / "Example.twbx"
            xml = (
                b'<workbook version="2026.1"><datasources/><worksheets>'
                b'<worksheet name="Sheet 1"/></worksheets><dashboards/></workbook>'
            )
            with zipfile.ZipFile(twbx, "w") as archive:
                archive.writestr("Example.twb", xml)
            original_project = build_dataset.PROJECT
            try:
                build_dataset.PROJECT = root
                record = build_dataset.inspect_workbook(
                    "Example", twbx, root / "dataset" / "workbooks"
                )
            finally:
                build_dataset.PROJECT = original_project
            self.assertEqual(record["status"], "available")
            self.assertTrue(record["integrity"]["valid"])
            self.assertEqual(record["twb"]["features"]["worksheet_count"], 1)
            self.assertTrue((root / record["twb"]["path"]).exists())


if __name__ == "__main__":
    unittest.main()
