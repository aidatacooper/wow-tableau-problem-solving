"""Validate one contributed iteration, then run its builder and verifier."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

import yaml

try:
    from scripts.case_catalogue import check_catalogue, validate_identity
except ModuleNotFoundError:
    from case_catalogue import check_catalogue, validate_identity


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
    metadata = case_dir / "case.yaml"
    if not metadata.is_file():
        raise AssertionError("Missing required files: case.yaml")
    case = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
    if case.get("schema_version") == "legacy-summary-1.0":
        validate_identity(case_dir, case, LAB_ROOT)
        return case
    missing = [name for name in REQUIRED_FILES if not (case_dir / name).is_file()]
    if missing:
        raise AssertionError(f"Missing required files: {', '.join(missing)}")

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
    # A visual claim needs a visual artifact. Without this, a case can assert
    # acceptable_delta with no rendered image behind it and still pass every
    # other check, which is exactly how an empty-rendering workbook slipped
    # through once. Historical schema 1.0 records are grandfathered.
    if (
        case["visual_status"] != "not_evaluated"
        and case.get("verification_status") != "historical"
    ):
        artifacts = case.get("artifacts") or {}
        for key in ("cloud_author", "cloud_replica"):
            relative = artifacts.get(key)
            if not relative:
                raise AssertionError(
                    f"visual_status '{case['visual_status']}' requires artifacts.{key}"
                )
            if not (case_dir / relative).is_file():
                raise AssertionError(
                    f"artifacts.{key} does not exist: {relative}"
                )
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

    records = [*lock.get("extracted_data", []), *lock.get("derived_data", [])]
    locked = {item["file"]: item for item in records}
    if len(locked) != len(records):
        raise AssertionError("Source lock contains duplicate data paths")
    declared = set(case["inputs"].get("data_files", []))
    if not declared or declared != set(locked):
        raise AssertionError("case.yaml data_files must match source-lock.json")

    for relative, record in locked.items():
        path = case_dir / relative
        if not path.is_file():
            raise AssertionError(f"Missing extracted data: {relative}")
        if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise AssertionError(f"Extracted data hash mismatch: {relative}")


def sdk_boundary_violations(source: str) -> list[str]:
    """Inspect executable Python, allowing empty templates and public SDK APIs.

    This is an authoring contract check, not a security sandbox. Analysis and
    verifier scripts may inspect XML; case construction must use the SDK.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"builder has invalid Python at line {exc.lineno}: {exc.msg}"]
    violations: set[str] = set()
    forbidden_modules = ("lxml", "xml.etree")
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            modules = [module, *[f"{module}.{alias.name}" for alias in node.names]]
        for module in modules:
            if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden_modules):
                violations.add(f"line {node.lineno}: builder imports raw XML library {module}; use public cwtwb APIs")
        if isinstance(node, ast.Attribute) and node.attr in {"root", "_datasource", "_field_registry"}:
            violations.add(f"line {node.lineno}: builder accesses workbook internals .{node.attr}; use public cwtwb APIs")
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Attribute) and function.attr in {"SubElement", "Element", "fromstring", "tostring"}:
                # Raw XML constructors are disallowed even if an import is aliased.
                violations.add(f"line {node.lineno}: builder calls raw XML operation {function.attr}; use public cwtwb APIs")
    return sorted(violations)


def public_sdk_boundary_required(case: dict) -> bool:
    """Apply the new construction contract to migrated, nonhistorical cases."""
    return case.get("schema_version") == "1.1.0" and case.get("verification_status") != "historical"


def validate_builder_boundary(case_dir: Path, *, enforce_public_sdk: bool = True) -> None:
    build_files = [
        path
        for path in case_dir.rglob("*.py")
        if path.name != "verify_replication.py"
    ]
    violations = []
    for path in build_files:
        source = path.read_text(encoding="utf-8")
        if enforce_public_sdk:
            violations.extend(f"{path.relative_to(case_dir)}: {reason}" for reason in sdk_boundary_violations(source))
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
    # Repository text fixtures are UTF-8, including legacy case scripts. Windows
    # otherwise decodes them with the machine's locale (for example GBK).
    environment = {**os.environ, "PYTHONUTF8": "1"}
    subprocess.run(
        [sys.executable, str(case_dir / filename)],
        cwd=LAB_ROOT,
        check=True,
        env=environment,
    )


def run_case_scripts_isolated(case_dir: Path) -> None:
    """Rebuild and verify a fresh copy without replacing Cloud-reviewed artifacts.

    CI may regenerate random workbook IDs, archive timestamps and local paths.
    Those bytes are validation output, not a replacement for the published capture.
    Exceptions propagate and temporary output is discarded on success or failure.
    """
    with tempfile.TemporaryDirectory(prefix="wow-case-validation-") as directory:
        scratch_root = Path(directory) / "lab"
        scratch_case = scratch_root / "iterations" / case_dir.name
        shutil.copytree(case_dir, scratch_case, ignore=shutil.ignore_patterns("__pycache__", ".roundtrip*"))
        # A published capture binds the accepted UUID/hash, not this fresh build.
        # Verify the rebuild's data and contracts without treating copied REST
        # evidence as a capture of its newly generated workbook identity.
        cloud_manifest = scratch_case / "evidence/cloud-verification.json"
        accepted_manifest = cloud_manifest.read_bytes() if cloud_manifest.exists() else None
        if accepted_manifest is not None:
            cloud_manifest.unlink()
        # A no-op builder must not accidentally verify a copied accepted workbook.
        for artifact in (scratch_case / "outputs").rglob("*"):
            if artifact.is_file() and artifact.suffix.lower() in WORKBOOK_SUFFIXES:
                artifact.unlink()
        run_case_script(scratch_case, "build_replication.py")
        metadata = yaml.safe_load((scratch_case / "case.yaml").read_text(encoding="utf-8")) or {}
        validate_workbook_schema(scratch_case, metadata)
        primary = metadata.get("artifacts", {}).get("primary_workbook", "outputs/replicated-workbook.twbx")
        case_file(scratch_case, primary, "Builder did not generate its primary workbook")
        # Historical verifiers may use a declared former output name. Point that
        # name at the fresh build in scratch, never at copied historical bytes.
        temporary_aliases = []
        for alias, target in metadata.get("artifact_aliases", {}).items():
            alias_path, target_path = Path(alias), Path(target)
            if alias_path.suffix.lower() not in WORKBOOK_SUFFIXES:
                continue
            if alias_path.is_absolute() or ".." in alias_path.parts or not alias_path.parts or alias_path.parts[0] != "outputs":
                raise AssertionError("Workbook artifact aliases must stay under outputs/")
            source = case_file(scratch_case, target_path, "Workbook artifact alias requires a rebuilt target")
            destination = scratch_case / alias_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            temporary_aliases.append(destination)
        run_case_script(scratch_case, "verify_replication.py")
        if accepted_manifest is not None:
            cloud_manifest.write_bytes(accepted_manifest)
        for alias in temporary_aliases:
            alias.unlink()
        # Archival author/probe files are metadata evidence, not build inputs.
        # Restore them only after the fresh verifier has succeeded. Never restore
        # a primary output, a declared alias, or a missing generated companion.
        current_paths = {primary, *metadata.get("artifact_aliases", {}).keys(), *metadata.get("artifact_aliases", {}).values()}
        for record in metadata.get("historical_artifacts", []):
            relative = record.get("path")
            if record.get("role") not in {"author_source", "probe"} or relative in current_paths:
                continue
            path = Path(str(relative))
            if path.suffix.lower() not in WORKBOOK_SUFFIXES:
                continue
            original = case_file(case_dir, relative, "Historical archive evidence is missing")
            destination = scratch_case / path
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, destination)
        case = validate_metadata(scratch_case)
        validate_source_lock(scratch_case, case)
        validate_builder_boundary(scratch_case, enforce_public_sdk=public_sdk_boundary_required(case))
        validate_identity(scratch_case, case, LAB_ROOT)


def validate_workbook_schema(case_dir: Path, case: dict) -> None:
    """Reject generated workbooks that violate Tableau's own TWB XSD.

    Tableau Desktop refuses to load a workbook whose DOM loader hits an
    out-of-order XSD sequence (for example ``<column-instance>`` after
    ``<drill-paths>`` or ``<action>`` after ``<edit-parameter-action>``).
    Static contract checks in the verifier do not catch this, so the packaged
    artifact is checked directly against the vendored official schema.

    Compatibility-only warnings that Tableau itself tolerates are ignored;
    only strict schema errors fail the case.
    """
    primary = case.get("artifacts", {}).get(
        "primary_workbook", "outputs/replicated-workbook.twbx"
    )
    workbook = case_dir / str(primary)
    if workbook.suffix.lower() not in WORKBOOK_SUFFIXES or not workbook.is_file():
        return
    try:
        from cwtwb.validator import (
            load_workbook_root,
            validate_against_schema,
        )
    except ModuleNotFoundError:
        return
    try:
        root = load_workbook_root(workbook)
    except Exception:
        # Fixtures and non-archive placeholders are covered by the verifier.
        return
    result = validate_against_schema(root)
    if not result.schema_available:
        return
    if result.errors:
        details = "\n".join(f"  * {error}" for error in result.errors)
        raise AssertionError(
            f"Generated workbook fails Tableau TWB XSD validation ({primary}):\n{details}"
        )


def validate_iteration(case_dir: Path, run_scripts: bool = True) -> None:
    case_dir = case_dir.resolve()
    case = validate_metadata(case_dir)
    if case["schema_version"] == "legacy-summary-1.0":
        # Historical summaries are identity contracts, not retrospective v1 claims.
        # In particular, metadata migration must never rebuild legacy workbooks.
        validate_identity(case_dir, case, LAB_ROOT)
        check_catalogue(LAB_ROOT)
        return
    validate_unique_identity(case_dir, case)
    validate_source_lock(case_dir, case)
    validate_builder_boundary(case_dir, enforce_public_sdk=public_sdk_boundary_required(case))
    if run_scripts:
        run_case_script(case_dir, "build_replication.py")
        validate_workbook_schema(case_dir, case)
        run_case_script(case_dir, "verify_replication.py")
    # A new case has no packaged output until its first build succeeds.
    validate_identity(case_dir, case, LAB_ROOT)
    check_catalogue(LAB_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    validate_iteration(args.case_dir, run_scripts=not args.metadata_only)
    print(f"PASS: {args.case_dir}")


if __name__ == "__main__":
    main()
