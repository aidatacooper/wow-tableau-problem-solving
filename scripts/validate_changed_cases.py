"""Run validation for iteration directories changed by a pull request."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

from validate_iteration import LAB_ROOT, run_case_scripts_isolated, validate_iteration
from case_catalogue import active_cases, check_catalogue


ITERATIONS_PREFIX = "iterations/"


def changed_iterations(base_ref: str) -> list[Path]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=LAB_ROOT,
        text=True,
    )
    names = {
        Path(line).parts[1]
        for line in output.splitlines()
        if line.startswith(ITERATIONS_PREFIX)
        and len(Path(line).parts) > 1
        and Path(line).parts[1] != "_template"
    }
    return [LAB_ROOT / "iterations" / name for name in sorted(names)]


def all_v1_iterations() -> list[Path]:
    return [directory for directory, _ in active_cases(LAB_ROOT)]


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base-ref")
    source.add_argument("--all", action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    check_catalogue(LAB_ROOT)
    cases = all_v1_iterations() if args.all else changed_iterations(args.base_ref)
    if not cases:
        print("No contributed iteration changed")
        return
    for case in cases:
        if not case.exists():
            # Removed/archived cases are checked by the active catalogue above.
            continue
        metadata = case / "case.yaml"
        if not metadata.is_file():
            raise AssertionError(
                f"Legacy or deleted iteration changed without migration: {case.name}"
            )
        document = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
        if "functional_status" not in document:
            raise AssertionError(
                f"Legacy iteration changed without v1 migration: {case.name}"
            )
        # Validate committed Cloud evidence first, then independently rebuild in
        # a disposable copy. Direct validate_iteration retains its authoring flow.
        validate_iteration(case, run_scripts=False)
        if not args.metadata_only and document.get("schema_version") != "legacy-summary-1.0":
            run_case_scripts_isolated(case)
        print(f"PASS: {case.name}")


if __name__ == "__main__":
    main()
