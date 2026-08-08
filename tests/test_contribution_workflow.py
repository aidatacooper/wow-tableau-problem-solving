import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


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
    path = iteration / "case.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("analysis_status: in_progress", "analysis_status: completed")
    text = text.replace(
        "replace_with_an_observable_functional_scenario",
        "generated_workbook_opens",
    )
    path.write_text(text, encoding="utf-8")


class ContributionWorkflowTests(unittest.TestCase):
    def test_prepare_case_extracts_data_and_never_copies_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Workbook.twb", "<workbook/>")
                archive.writestr("Data/Datasources/orders.hyper", b"hyper-data")

            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-example",
                case_id="example-case",
                post="posts/example.html",
                iterations_root=root / "iterations",
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
            validate_iteration.validate_iteration(iteration, run_scripts=True)

    def test_prepare_case_rejects_archive_without_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Workbook.twb", "<workbook/>")

            with self.assertRaisesRegex(ValueError, "No packaged data"):
                prepare_case.prepare_case(
                    source=source,
                    iteration_id="2026-01-01-no-data",
                    case_id="example-case",
                    post="posts/example.html",
                    iterations_root=root / "iterations",
                )
            self.assertFalse((root / "iterations" / "2026-01-01-no-data").exists())

    def test_validator_rejects_builder_source_workbook_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "author.twbx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Data/orders.hyper", b"hyper-data")
            iteration = prepare_case.prepare_case(
                source=source,
                iteration_id="2026-01-01-forbidden",
                case_id="example-case",
                post="posts/example.html",
                iterations_root=root / "iterations",
            )
            (iteration / "build_replication.py").write_text(
                "SOURCE_TWBX = 'author.twbx'\n", encoding="utf-8"
            )
            complete_case_metadata(iteration)

            with self.assertRaisesRegex(AssertionError, "SOURCE_TWBX"):
                validate_iteration.validate_iteration(iteration, run_scripts=False)


if __name__ == "__main__":
    unittest.main()
