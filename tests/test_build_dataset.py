import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile

import yaml
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
        # Selection ownership is independent of completion. Published status must
        # reflect the editable case metadata, including honest partial results.
        records = {item["case_id"]: item for item in registry["consumed_cases"]}
        project = Path(__file__).resolve().parents[1]
        for item in selected[:3]:
            canonical = registry["legacy_case_ids"][item["case_id"]]
            metadata_path = project / "iterations" / records[canonical]["iteration"] / "case.yaml"
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(statuses[canonical], metadata["functional_status"])


    def test_case_id_is_stable_and_date_scoped(self):
        url = "https://donnacoles.home.blog/2026/02/15/example/"
        actual = build_dataset.stable_case_id(url, "2026-02-15")
        expected_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        self.assertEqual(actual, f"donna-2026-02-15-{expected_hash}")

    def alias_registry(self):
        return {
            "schema_version": "2.0.0",
            "legacy_case_ids": {"donna-old": "wow-2026-ww01-example"},
            "consumed_cases": [{
                "case_id": "wow-2026-ww01-example", "status": "consumed",
                "legacy_case_ids": {"donna-old": "wow-2026-ww01-example"},
                "workbook_ids": [],
            }],
        }

    def test_canonical_and_alias_selection_counts_one_case(self):
        registry = self.alias_registry()
        selected = [{"case_id": value} for value in (
            "donna-old", "wow-2026-ww01-example", "donna-unrelated")]
        self.assertEqual(build_dataset.eligible_cases(selected, registry), selected[-1:])
        self.assertEqual(len(build_dataset.canonical_consumed_case_ids(registry)), 1)
        self.assertEqual(len(build_dataset.consumed_case_ids(registry)), 2)
        self.assertEqual(selected[0]["case_id"], "donna-old")

    def test_partial_consumed_case_is_excluded_without_promoting_status(self):
        registry = self.alias_registry()
        registry["consumed_cases"][0]["replication_status"] = "partial"
        snapshot = json.dumps(registry, sort_keys=True)
        selected = [{"case_id": "donna-old"},
                    {"case_id": "wow-2026-ww01-example"},
                    {"case_id": "new-candidate"}]
        self.assertEqual(build_dataset.eligible_cases(selected, registry), selected[-1:])
        self.assertEqual(registry["consumed_cases"][0]["replication_status"], "partial")
        self.assertEqual(json.dumps(registry, sort_keys=True), snapshot)

    def test_invalid_aliases_fail_closed_without_filtering_unrelated_cases(self):
        for mapping in ({"donna-unrelated": "unknown"}, ["donna-old"],
                        {" donna-old": "wow-2026-ww01-example"},
                        {"wow-2026-ww01-example": "wow-2026-ww01-example"}):
            with self.subTest(mapping=mapping):
                registry = self.alias_registry()
                registry["legacy_case_ids"] = mapping
                with self.assertRaises(ValueError):
                    build_dataset.eligible_cases([{"case_id": "donna-unrelated"}], registry)
        registry = self.alias_registry()
        registry["consumed_cases"][0]["legacy_case_ids"] = {"donna-unrelated": "unknown"}
        with self.assertRaises(ValueError):
            build_dataset.consumed_case_ids(registry)

    def test_undeclared_global_alias_cannot_suppress_unrelated_source(self):
        registry = self.alias_registry()
        registry["legacy_case_ids"]["donna-unrelated"] = "wow-2026-ww01-example"
        with self.assertRaisesRegex(ValueError, "must match canonical record aliases"):
            build_dataset.eligible_cases([{"case_id": "donna-unrelated"}], registry)

    def test_dataset_verification_resolves_alias_and_reports_unknown_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset"
            (dataset / "cases/donna-old").mkdir(parents=True)
            source = {"case_id": "donna-old", "tableau_links": []}
            (dataset / "cases/donna-old/case.json").write_text(json.dumps(source))
            (dataset / "cases.jsonl").write_text(json.dumps(source) + "\n")
            (dataset / "workbooks.jsonl").write_text("")
            for filename in ("dataset.json", "quality-report.json"):
                (dataset / filename).write_text("{}")
            registry = self.alias_registry()
            (dataset / "usage.json").write_text(json.dumps(registry))
            self.assertEqual(build_dataset.check_dataset(root), [])
            registry["legacy_case_ids"] = {"donna-old": "unknown"}
            (dataset / "usage.json").write_text(json.dumps(registry))
            errors = build_dataset.check_dataset(root)
            self.assertTrue(any("Invalid or conflicting case alias" in error for error in errors))
            self.assertTrue(any("Unknown consumed case_id" in error for error in errors))

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
