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
}
WORKBOOK_SUFFIXES = {".twb", ".twbx"}
ACCEPTANCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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
        "schema_version",
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
    if case["schema_version"] not in {"1.0.0", "1.1.0"}:
        raise AssertionError("Unsupported case schema_version")
    if case["iteration_id"] != case_dir.name:
        raise AssertionError("case.yaml iteration_id must match the directory name")
    if case["analysis_status"] != "completed":
        raise AssertionError("analysis_status must be completed before submission")
    if not case["acceptance"] or any(
        marker in str(case["acceptance"])
        for marker in ("replace_with_", "replace-with-")
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
    validate_status_invariants(case)
    validate_acceptance(case_dir, case)
    validate_cwtwb_runs(case_dir, case)
    return case


def validate_status_invariants(case: dict) -> None:
    functional = case["functional_status"]
    cwtwb_result = case["cwtwb_result"]
    if functional == "replicated" and cwtwb_result == "blocked":
        raise AssertionError("replicated cases cannot have a blocked cwtwb result")
    if case["schema_version"] == "1.0.0":
        return
    if functional in {"partial", "blocked"} and not real_value(
        case.get("remaining_work")
    ):
        raise AssertionError(f"{functional} cases must describe remaining_work")
    if (functional == "blocked" or cwtwb_result == "blocked") and not real_value(
        case.get("blocker")
    ):
        raise AssertionError("blocked cases must describe the blocker")
    if cwtwb_result == "workaround" and not case.get("workarounds"):
        raise AssertionError("cwtwb_result workaround requires workarounds")
    if cwtwb_result == "blocked" and not real_value(case.get("capability_gaps")):
        raise AssertionError("cwtwb_result blocked requires capability_gaps")


def real_value(value: object) -> bool:
    return bool(value) and "replace with" not in str(value).casefold()


def case_file(case_dir: Path, relative: object, message: str) -> Path:
    path = Path(str(relative))
    if path.is_absolute() or ".." in path.parts or not (case_dir / path).is_file():
        raise AssertionError(message)
    return case_dir / path


def validate_acceptance(case_dir: Path, case: dict) -> None:
    """Validate traceable acceptance entries while retaining v1.0 strings."""
    if case.get("schema_version") != "1.1.0":
        return
    verifier = (case_dir / "verify_replication.py").read_text(encoding="utf-8")
    seen: set[str] = set()
    for item in case["acceptance"]:
        if not isinstance(item, dict):
            raise AssertionError("schema 1.1 acceptance entries must be mappings")
        acceptance_id = item.get("id", "")
        if not ACCEPTANCE_ID.fullmatch(acceptance_id) or acceptance_id in seen:
            raise AssertionError(f"Invalid or duplicate acceptance id: {acceptance_id}")
        seen.add(acceptance_id)
        if not item.get("description"):
            raise AssertionError(f"Acceptance {acceptance_id} needs a description")
        mode = item.get("mode")
        if mode == "automated":
            if acceptance_id not in verifier:
                raise AssertionError(
                    f"Automated acceptance {acceptance_id} is not named in verifier"
                )
        elif mode == "manual":
            evidence = item.get("evidence")
            case_file(
                case_dir,
                evidence,
                f"Manual acceptance {acceptance_id} needs an evidence file",
            )
        else:
            raise AssertionError(
                f"Acceptance {acceptance_id} mode must be automated or manual"
            )


def validate_cwtwb_runs(case_dir: Path, case: dict) -> None:
    """Keep retest history appendable without breaking existing v1.0 cases."""
    runs = case["cwtwb"].get("runs")
    if case.get("schema_version") == "1.1.0" and not runs:
        raise AssertionError("schema 1.1 cases require cwtwb.runs")
    if not runs:
        return
    for run in runs:
        if run.get("result") not in {"pass", "workaround", "blocked"}:
            raise AssertionError("Each cwtwb run needs a valid result")
        evidence = run.get("evidence")
        if not run.get("version"):
            raise AssertionError("Each cwtwb run needs a version and evidence file")
        case_file(
            case_dir,
            evidence,
            "Each cwtwb run needs a version and evidence file",
        )
    latest = runs[-1]
    if latest["version"] != case["cwtwb"]["tested_version"]:
        raise AssertionError("Latest cwtwb run must match cwtwb.tested_version")
    if latest["result"] != case["cwtwb_result"]:
        raise AssertionError("Latest cwtwb run must match cwtwb_result")


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
