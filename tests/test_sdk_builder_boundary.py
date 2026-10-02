"""Synthetic authoring-boundary fixtures: no author workbooks or data needed."""
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
