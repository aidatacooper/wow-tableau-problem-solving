"""Synthetic authoring-boundary fixtures: no author workbooks or data needed."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_iteration as validation

from scripts.validate_iteration import validate_builder_boundary


class SDKBuilderBoundaryTests(unittest.TestCase):
    def check_source(self, source):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / "build_replication.py").write_text(source, encoding="utf-8")
            validate_builder_boundary(case)

    def test_public_sdk_and_empty_template_are_allowed(self):
        self.check_source("from cwtwb import TWBEditor\neditor = TWBEditor('')\neditor.add_worksheet('Sales')\neditor.configure_chart('Sales', mark_type='Bar')\n")

    def test_empty_template_path_is_allowed(self):
        self.check_source("from pathlib import Path\nfrom cwtwb import TWBEditor\neditor = TWBEditor(Path('empty-template.twb'))\n")

    def test_comments_do_not_trigger_xml_ast_check(self):
        self.check_source("# Avoid lxml.etree.SubElement and editor.root\nmessage = 'Use public APIs instead of editor._datasource'\n")

    def test_raw_xml_import_aliases_are_rejected(self):
        for source in ["from lxml import etree", "import lxml.etree as xml", "from xml.etree.ElementTree import SubElement as add", "from xml import etree"]:
            with self.subTest(source=source), self.assertRaisesRegex(AssertionError, "raw XML library"):
                self.check_source(source)

    def test_workbook_internals_are_rejected(self):
        for attribute in ["root", "_datasource", "_field_registry"]:
            with self.subTest(attribute=attribute), self.assertRaisesRegex(AssertionError, "workbook internals"):
                self.check_source(f"editor.{attribute}.find('table')")

    def test_raw_xml_operation_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "raw XML operation"):
            self.check_source("xml.SubElement(parent, 'pane')")

    def test_verifier_xml_analysis_is_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / "build_replication.py").write_text("from cwtwb import TWBEditor\neditor = TWBEditor('')", encoding="utf-8")
            (case / "verify_replication.py").write_text("from lxml import etree", encoding="utf-8")
            validate_builder_boundary(case)

    def test_local_helper_xml_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / "build_replication.py").write_text("import helper", encoding="utf-8")
            (case / "helper.py").write_text("from lxml import etree", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "helper.py"):
                validate_builder_boundary(case)

    def test_historical_compatibility_keeps_author_dependency_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            builder = case / "build_replication.py"
            builder.write_text("from lxml import etree", encoding="utf-8")
            validation_args = {"enforce_public_sdk": False}
            validate_builder_boundary(case, **validation_args)
            builder.write_text("SOURCE_TWBX = 'author.twbx'", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "SOURCE_TWBX"):
                validate_builder_boundary(case, **validation_args)

    def test_schema_migration_activates_public_sdk_ast_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / "build_replication.py").write_text("from lxml import etree", encoding="utf-8")
            for schema in ["1.0.0", "1.1.0"]:
                with self.subTest(schema=schema), patch.object(validation, "validate_metadata", return_value={"schema_version": schema}), patch.object(validation, "validate_unique_identity"), patch.object(validation, "validate_source_lock"), patch.object(validation, "validate_identity"), patch.object(validation, "check_catalogue"):
                    if schema == "1.0.0":
                        validation.validate_iteration(case, run_scripts=False)
                    else:
                        with self.assertRaisesRegex(AssertionError, "raw XML library"):
                            validation.validate_iteration(case, run_scripts=False)

    def test_explicit_historical_record_keeps_original_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            builder = case / "build_replication.py"
            builder.write_text("from lxml import etree", encoding="utf-8")
            document = {"schema_version": "1.1.0", "verification_status": "historical"}
            with patch.object(validation, "validate_metadata", return_value=document), patch.object(validation, "validate_unique_identity"), patch.object(validation, "validate_source_lock"), patch.object(validation, "validate_identity"), patch.object(validation, "check_catalogue"):
                validation.validate_iteration(case, run_scripts=False)
                builder.write_text("SOURCE_TWBX = 'author.twbx'", encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "SOURCE_TWBX"):
                    validation.validate_iteration(case, run_scripts=False)

    def test_ten_migrated_cloud_cases_require_public_sdk_construction(self):
        import yaml
        case_ids = {"wow-2019-ww29-high-orders", "wow-2019-ww30-navigation-kpi", "wow-2019-ww31-hub-spoke-map", "wow-2019-ww32-step-area-chart", "wow-2019-ww33-table-formatting", "wow-2019-ww34-top-n-single-worksheet", "wow-2019-ww36-custom-axis-tracker", "wow-2026-ww04-dynamic-moving-average", "wow-2026-ww05-kpi-period-comparison", "wow-2026-ww06-null-safe-averages"}
        found = set()
        root = Path(__file__).resolve().parents[1]
        for metadata in (root / "iterations").glob("*/case.yaml"):
            document = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
            if document.get("case_id") in case_ids:
                found.add(document["case_id"])
                self.assertEqual(document["schema_version"], "1.1.0")
                self.assertNotEqual(document.get("verification_status"), "historical")
                self.assertTrue(validation.public_sdk_boundary_required(document))
        self.assertEqual(found, case_ids)


if __name__ == "__main__":
    unittest.main()
