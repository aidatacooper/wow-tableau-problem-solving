"""CI rebuilds independently without replacing reviewed artifact bytes."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_iteration as validation


class IsolatedCaseValidationTests(unittest.TestCase):
    def make_case(self, root):
        case = root / "iterations" / "2026-01-01-ww01-example"
        (case / "outputs").mkdir(parents=True)
        (case / "outputs/replicated-workbook.twbx").write_bytes(b"accepted Cloud workbook")
        (case / "outputs/cloud-replica.png").write_bytes(b"accepted image")
        (case / "build_replication.py").write_text("# synthetic public SDK builder")
        (case / "verify_replication.py").write_text("# synthetic verifier")
        (case / "case.yaml").write_text("artifact_aliases:\n  outputs/former-name.twbx: outputs/replicated-workbook.twbx\n")
        return case

    def test_fresh_rebuild_preserves_original_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            visited = []
            def run(scratch, filename):
                self.assertNotEqual(scratch, case)
                visited.append((scratch, filename))
                artifact = scratch / "outputs/replicated-workbook.twbx"
                if filename == "build_replication.py":
                    self.assertFalse(artifact.exists())
                    artifact.write_bytes(b"new random IDs and paths")
                else:
                    self.assertEqual(artifact.read_bytes(), b"new random IDs and paths")
                    self.assertEqual((scratch / "outputs/former-name.twbx").read_bytes(), artifact.read_bytes())
                    (scratch / "outputs/new-evidence.json").write_text("verified")
            with patch.object(validation, "run_case_script", side_effect=run), patch.object(validation, "validate_metadata", return_value={}), patch.object(validation, "validate_source_lock"), patch.object(validation, "validate_builder_boundary"), patch.object(validation, "validate_identity"):
                validation.run_case_scripts_isolated(case)
            self.assertEqual([name for _, name in visited], ["build_replication.py", "verify_replication.py"])
            self.assertFalse(visited[0][0].exists())
            self.assertEqual((case / "outputs/replicated-workbook.twbx").read_bytes(), b"accepted Cloud workbook")
            self.assertEqual((case / "outputs/cloud-replica.png").read_bytes(), b"accepted image")
            self.assertFalse((case / "outputs/new-evidence.json").exists())

    def test_failed_build_preserves_original_and_propagates_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            visited = []
            def fail(scratch, filename):
                visited.append(scratch)
                (scratch / "outputs/new-evidence.json").write_text("failed")
                raise subprocess.CalledProcessError(1, filename)
            with patch.object(validation, "run_case_script", side_effect=fail):
                with self.assertRaises(subprocess.CalledProcessError):
                    validation.run_case_scripts_isolated(case)
            self.assertFalse(visited[0].exists())
            self.assertEqual((case / "outputs/replicated-workbook.twbx").read_bytes(), b"accepted Cloud workbook")
            self.assertFalse((case / "outputs/new-evidence.json").exists())

    def test_no_op_builder_cannot_pass_using_accepted_primary(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            with patch.object(validation, "run_case_script") as scripts:
                with self.assertRaisesRegex(AssertionError, "primary workbook"):
                    validation.run_case_scripts_isolated(case)
                self.assertEqual(scripts.call_count, 1)
            self.assertEqual((case / "outputs/replicated-workbook.twbx").read_bytes(), b"accepted Cloud workbook")

    def test_archival_probe_restored_only_after_fresh_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            (case / "outputs/probe.twbx").write_bytes(b"archival probe")
            (case / "case.yaml").write_text("historical_artifacts:\n- path: outputs/probe.twbx\n  role: probe\n")
            def run(scratch, filename):
                self.assertFalse((scratch / "outputs/probe.twbx").exists())
                if filename == "build_replication.py":
                    (scratch / "outputs/replicated-workbook.twbx").write_bytes(b"fresh primary")
            def identity(scratch, document, root):
                self.assertEqual((scratch / "outputs/probe.twbx").read_bytes(), b"archival probe")
                self.assertEqual((scratch / "outputs/replicated-workbook.twbx").read_bytes(), b"fresh primary")
            with patch.object(validation, "run_case_script", side_effect=run), patch.object(validation, "validate_metadata", return_value={}), patch.object(validation, "validate_source_lock"), patch.object(validation, "validate_builder_boundary"), patch.object(validation, "validate_identity", side_effect=identity):
                validation.run_case_scripts_isolated(case)


if __name__ == "__main__":
    unittest.main()
