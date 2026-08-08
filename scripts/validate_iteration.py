"""Validate one contributed iteration, then run its builder and verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


LAB_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "case.yaml",
    "analysis.md",
    "build_replication.py",
    "verify_replication.py",
    "inputs/source-lock.json",
)
FORBIDDEN_BUILD_PATTERNS = {
    r"\bSOURCE_TWBX\b": "builder references SOURCE_TWBX",
    r"\bsource_workbook\b": "builder references source_workbook",
    r"open_existing\s*\(": "builder opens an existing workbook",
    r"[\"']dashboards[\\/]": "builder reads the local author-workbook archive",
    r"(?:zipfile\.)?ZipFile\s*\(": "builder opens a workbook archive directly",
}
WORKBOOK_SUFFIXES = {".twb", ".twbx"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_metadata(case_dir: Path) -> dict:
    missing = [name for name in REQUIRED_FILES if not (case_dir / name).is_file()]
    if missing:
        raise AssertionError(f"Missing required files: {', '.join(missing)}")

    case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    required = {
        "case_id",
        "iteration_id",
        "post",
        "cwtwb",
        "analysis_status",
        "functional_status",
        "visual_status",
        "cwtwb_result",
        "inputs",
        "acceptance",
    }
    absent = sorted(required - set(case or {}))
    if absent:
        raise AssertionError(f"case.yaml missing keys: {', '.join(absent)}")
    if case["iteration_id"] != case_dir.name:
        raise AssertionError("case.yaml iteration_id must match the directory name")
    if case["analysis_status"] != "completed":
        raise AssertionError("analysis_status must be completed before submission")
    if not case["acceptance"] or any(
        "replace_with_" in str(item) for item in case["acceptance"]
    ):
        raise AssertionError("case.yaml acceptance must contain real scenarios")
    if case["functional_status"] not in {"partial", "replicated", "blocked"}:
        raise AssertionError("Invalid functional_status")
    if case["visual_status"] not in {
        "not_evaluated",
        "acceptable_delta",
        "matched",
    }:
        raise AssertionError("Invalid visual_status")
    if case["cwtwb_result"] not in {"pass", "workaround", "blocked"}:
        raise AssertionError("Invalid cwtwb_result")
    if not case["cwtwb"].get("tested_version"):
        raise AssertionError("cwtwb.tested_version is required")
    return case


def validate_source_lock(case_dir: Path, case: dict) -> None:
    lock_path = case_dir / "inputs" / "source-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("source_workbook_used_by_builder") is not False:
        raise AssertionError("source_workbook_used_by_builder must be false")

    locked = {item["file"]: item for item in lock.get("extracted_data", [])}
    declared = set(case["inputs"].get("data_files", []))
    if not declared or declared != set(locked):
        raise AssertionError("case.yaml data_files must match source-lock.json")

    for relative, record in locked.items():
        path = case_dir / relative
        if not path.is_file():
            raise AssertionError(f"Missing extracted data: {relative}")
        if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise AssertionError(f"Extracted data hash mismatch: {relative}")


def validate_builder_boundary(case_dir: Path) -> None:
    build_files = [
        path
        for path in case_dir.rglob("*.py")
        if path.name != "verify_replication.py"
    ]
    violations = []
    for path in build_files:
        source = path.read_text(encoding="utf-8")
        violations.extend(
            f"{path.relative_to(case_dir)}: {reason}"
            for pattern, reason in FORBIDDEN_BUILD_PATTERNS.items()
            if re.search(pattern, source, flags=re.IGNORECASE)
        )
    if violations:
        raise AssertionError("; ".join(violations))

    misplaced = [
        str(path.relative_to(case_dir))
        for path in case_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in WORKBOOK_SUFFIXES
        and path.parent != case_dir / "outputs"
    ]
    if misplaced:
        raise AssertionError(
            "Author or generated workbooks must not be stored outside outputs/: "
            + ", ".join(misplaced)
        )


def validate_unique_identity(case_dir: Path, case: dict) -> None:
    for metadata in (LAB_ROOT / "iterations").glob("*/case.yaml"):
        if metadata.parent == case_dir:
            continue
        other = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
        if other.get("case_id") == case["case_id"]:
            raise AssertionError(
                f"case_id already belongs to {metadata.parent.name}"
            )
        if other.get("post") == case.get("post"):
            raise AssertionError(f"post already belongs to {metadata.parent.name}")

    usage_path = LAB_ROOT / "usage" / "consumed-cases.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8"))
    for item in usage.get("consumed_cases", []):
        if (
            item.get("case_id") == case["case_id"]
            and item.get("iteration") != case_dir.name
        ):
            raise AssertionError(
                f"case_id is already consumed by {item.get('iteration')}"
            )


def run_case_script(case_dir: Path, filename: str) -> None:
    subprocess.run(
        [sys.executable, str(case_dir / filename)],
        cwd=LAB_ROOT,
        check=True,
    )


def validate_iteration(case_dir: Path, run_scripts: bool = True) -> None:
    case_dir = case_dir.resolve()
    case = validate_metadata(case_dir)
    validate_unique_identity(case_dir, case)
    validate_source_lock(case_dir, case)
    validate_builder_boundary(case_dir)
    if run_scripts:
        run_case_script(case_dir, "build_replication.py")
        run_case_script(case_dir, "verify_replication.py")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    validate_iteration(args.case_dir, run_scripts=not args.metadata_only)
    print(f"PASS: {args.case_dir}")


if __name__ == "__main__":
    main()
