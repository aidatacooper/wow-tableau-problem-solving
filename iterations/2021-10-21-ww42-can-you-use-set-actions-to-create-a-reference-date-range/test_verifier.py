"""Mutation tests ensure the local oracle rejects meaningful regressions."""
import copy
import unittest
from unittest.mock import Mock, patch

from cwtwb.validator import load_workbook_root
from tableauhyperapi import Connection, HyperProcess, Telemetry
from verify_replication import OUTPUT, RAW, INITIAL, contracts, numerical_checks, sdk_revision


class InstalledSDKProvenanceTests(unittest.TestCase):
    def test_pip_vcs_install_uses_direct_url_without_git_checkout(self):
        distribution = Mock()
        distribution.read_text.return_value = '{"vcs_info":{"commit_id":"tested-commit"}}'
        with patch("verify_replication.Path.exists", return_value=False), patch("verify_replication.importlib.metadata.distribution", return_value=distribution):
            self.assertEqual(sdk_revision(), "tested-commit")

    def test_plain_wheel_does_not_invent_commit(self):
        distribution = Mock()
        distribution.read_text.return_value = None
        with patch("verify_replication.Path.exists", return_value=False), patch("verify_replication.importlib.metadata.distribution", return_value=distribution):
            self.assertIsNone(sdk_revision())


class OracleMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_workbook_root(OUTPUT)
        cls.process = HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={"log_config": ""})
        cls.connection = Connection(cls.process.endpoint, RAW)
        cls.rows = cls.connection.execute_list_query('SELECT "Order Date","State","Sales" FROM "Extract"."Extract"')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.process.close()

    def test_clear_selection_must_keep_state(self):
        root = copy.deepcopy(self.document)
        root.find("./actions/edit-group-action/params/param[@name='selection-clear-set-option']").set("value", "exclude-all")
        with self.assertRaises(AssertionError):
            contracts(root)

    def test_unmutated_contracts_pass(self):
        contracts(self.document)

    def test_reference_bounds_must_be_ordered(self):
        root = copy.deepcopy(self.document)
        lines = root.findall(".//worksheet[@name='Trend']//reference-line")
        lines[0].set("value-column", lines[1].get("value-column"))
        with self.assertRaises(AssertionError):
            contracts(root)

    def test_reference_bounds_must_be_bound_to_same_pane(self):
        root = copy.deepcopy(self.document)
        line = root.find(".//worksheet[@name='Trend']//reference-line")
        encodings = line.getparent().find("encodings")
        for lod in list(encodings.findall("lod")):
            encodings.remove(lod)
        with self.assertRaises(AssertionError):
            contracts(root)

    def test_text_table_addressing_cannot_fall_back_to_rows(self):
        root = copy.deepcopy(self.document)
        for calc in root.findall(".//worksheet[@name='Top States']//column-instance/table-calc"):
            calc.set("ordering-type", "Rows")
        with self.assertRaises(AssertionError):
            contracts(root)

    def test_peak_addressing_cannot_partition_by_month(self):
        root = copy.deepcopy(self.document)
        for calc in root.findall(".//worksheet[@name='Trend']//column-instance/table-calc"):
            calc.set("ordering-type", "Columns")
        with self.assertRaises(AssertionError):
            contracts(root)

    def test_wrong_aggregation_rejected(self):
        root = copy.deepcopy(self.document)
        calc = root.find("./datasources/datasource/column[@caption='Selected Total']/calculation")
        calc.set("formula", calc.get("formula").replace("SUM(", "AVG("))
        with self.assertRaises(AssertionError):
            numerical_checks(root, self.rows, self.connection, {"mutant": INITIAL})

    def test_reversed_rank_rejected(self):
        root = copy.deepcopy(self.document)
        calc = root.find("./datasources/datasource/column[@caption='State Rank']/calculation")
        calc.set("formula", calc.get("formula").replace("'desc'", "'asc'"))
        with self.assertRaises(AssertionError):
            numerical_checks(root, self.rows, self.connection, {"mutant": INITIAL})

    def test_wrong_share_denominator_rejected(self):
        root = copy.deepcopy(self.document)
        calc = root.find("./datasources/datasource/column[@caption='State Share']/calculation")
        calc.set("formula", "SUM([Sales]) / WINDOW_MAX(SUM([Sales]))")
        with self.assertRaises(AssertionError):
            numerical_checks(root, self.rows, self.connection, {"mutant": INITIAL})

    def test_selection_filter_regression_rejected(self):
        root = copy.deepcopy(self.document)
        root.find("./datasources/datasource/column[@caption='In Selection']/calculation").set("formula", "TRUE")
        with self.assertRaises(AssertionError):
            numerical_checks(root, self.rows, self.connection, {"mutant": INITIAL})


if __name__ == "__main__":
    unittest.main(verbosity=2)
