import importlib.util
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml


LAB_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prepare_case = load_module("prepare_case", LAB_ROOT / "scripts" / "prepare_case.py")
validate_iteration = load_module(
    "validate_iteration", LAB_ROOT / "scripts" / "validate_iteration.py"
)


def complete_case_metadata(iteration: Path) -> None:
    (iteration / "outputs").mkdir(exist_ok=True)
    (iteration / "outputs/replicated-workbook.twbx").write_bytes(b"synthetic artifact for metadata validation")
    path = iteration / "case.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["analysis_status"] = "completed"
    document["functional_status"] = "replicated"
    document["cwtwb_result"] = "pass"
    document["acceptance"] = [
        {
            "id": "generated-workbook-opens",
            "description": "The generated workbook opens.",
            "mode": "automated",
        }
    ]
    document["cwtwb"]["runs"][-1]["result"] = "pass"
    document.pop("remaining_work", None)
    document.pop("blocker", None)
    document["capability_gaps"] = []
    path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    verifier = iteration / "verify_replication.py"
    verifier.write_text(
        verifier.read_text(encoding="utf-8")
        + "\n# acceptance: generated-workbook-opens\n",
        encoding="utf-8",
    )


class ContributionWorkflowTests(unittest.TestCase):
    def test_derived_inputs_are_locked_and_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inputs").mkdir()
            original = root / "inputs/raw.csv"
            derived = root / "inputs/calendar.csv"
            original.write_bytes(b"raw\n")
            derived.write_bytes(b"zero-filled calendar\n")
            def record(path):
                return {
                    "file": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }

            lock = {
                "source_workbook_used_by_builder": False,
                "extracted_data": [record(original)],
                "derived_data": [record(derived)],
            }
            (root / "inputs/source-lock.json").write_text(
                json.dumps(lock), encoding="utf-8"
            )
            case = {"inputs": {"data_files": ["inputs/raw.csv", "inputs/calendar.csv"]}}
            validate_iteration.validate_source_lock(root, case)
            derived.write_bytes(b"tampered calendar\n")
            with self.assertRaisesRegex(AssertionError, "hash mismatch"):
                validate_iteration.validate_source_lock(root, case)

    def test_prepare_case_extracts_data_and_never_copies_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Workbook.twb", "<workbook/>")
                archive.writestr("Data/Datasources/orders.hyper", b"hyper-data")

            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-ww01-example",
                case_id=None,
                post="posts/example.html",
                iterations_root=root / "iterations",
                challenge_year=2026,
            )

            self.assertFalse((iteration / source.name).exists())
            self.assertEqual(
                (iteration / "inputs" / "orders.hyper").read_bytes(), b"hyper-data"
            )
            lock = json.loads(
                (iteration / "inputs" / "source-lock.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(lock["source_workbook_used_by_builder"])
            self.assertEqual(lock["extracted_data"][0]["file"], "inputs/orders.hyper")
            complete_case_metadata(iteration)
            (iteration / "outputs/replicated-workbook.twbx").unlink()
            validate_iteration.validate_iteration(iteration, run_scripts=True)
            self.assertTrue((iteration / "outputs/replicated-workbook.twbx").is_file())

    def test_prepare_case_rejects_archive_without_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Workbook.twb", "<workbook/>")

            with self.assertRaisesRegex(ValueError, "No packaged data"):
                prepare_case.prepare_case(
                    source=source,
                    iteration_id="2026-01-01-ww01-no-data",
                    case_id=None,
                    post="posts/example.html",
                    iterations_root=root / "iterations",
                    challenge_year=2026,
                )
            self.assertFalse((root / "iterations" / "2026-01-01-ww01-no-data").exists())

    def test_validator_rejects_builder_source_workbook_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Data/orders.hyper", b"hyper-data")
            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-ww01-forbidden",
                case_id=None,
                post="posts/example.html",
                iterations_root=root / "iterations",
                challenge_year=2026,
            )
            (iteration / "build_replication.py").write_text(
                "SOURCE_TWBX = 'author.twbx'\n", encoding="utf-8"
            )
            complete_case_metadata(iteration)

            with self.assertRaisesRegex(AssertionError, "SOURCE_TWBX"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)

    def test_tableau_workbook_name_supports_modern_and_legacy_urls(self):
        self.assertEqual(
            "Workbook_Name",
            prepare_case.tableau_workbook_name(
                "https://public.tableau.com/app/profile/user/viz/Workbook_Name/View"
            ),
        )
        self.assertEqual(
            "LegacyBook",
            prepare_case.tableau_workbook_name(
                "https://public.tableau.com/views/LegacyBook/Dashboard"
            ),
        )

    def test_validator_scans_helper_files_and_rejects_misplaced_workbooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Data/orders.hyper", b"hyper-data")
            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-ww01-boundary",
                case_id=None,
                post="https://example.test/post",
                iterations_root=root / "iterations",
                challenge_year=2026,
            )
            complete_case_metadata(iteration)
            (iteration / "helper.py").write_text(
                "source_workbook = 'author.twbx'\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(AssertionError, "helper.py"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)

            (iteration / "helper.py").unlink()
            (iteration / "build_replication.py").write_text(
                "from zipfile import ZipFile\n"
                "ZipFile('outputs/generated.twbx', 'w').close()\n",
                encoding="utf-8",
            )
            validate_iteration.validate_iteration(iteration, run_scripts=False)

            (iteration / "author.twbx").write_bytes(b"not allowed")
            with self.assertRaisesRegex(AssertionError, "outside outputs"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)

    def test_validator_enforces_status_and_retest_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Data/orders.hyper", b"hyper-data")
            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-ww01-state",
                case_id=None,
                post="https://example.test/post",
                iterations_root=root / "iterations",
                challenge_year=2026,
            )
            complete_case_metadata(iteration)
            metadata = iteration / "case.yaml"
            document = yaml.safe_load(metadata.read_text(encoding="utf-8"))

            document["functional_status"] = "partial"
            metadata.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "remaining_work"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)

            document["functional_status"] = "replicated"
            document["cwtwb"]["runs"][-1]["version"] = "0.25.0"
            metadata.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "tested_version"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)


if __name__ == "__main__":
    unittest.main()
