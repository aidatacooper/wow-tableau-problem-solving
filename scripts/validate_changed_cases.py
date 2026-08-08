"""Run validation for iteration directories changed by a pull request."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

from validate_iteration import LAB_ROOT, validate_iteration


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()
    cases = changed_iterations(args.base_ref)
    if not cases:
        print("No contributed iteration changed")
        return
    for case in cases:
        metadata = case / "case.yaml"
        if not metadata.is_file():
            print(f"LEGACY: {case.name} has no v1 case.yaml; no new files may depend on it")
            continue
        document = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
        if "functional_status" not in document:
            print(f"LEGACY: {case.name} predates the v1 contribution contract")
            continue
        validate_iteration(case)
        print(f"PASS: {case.name}")


if __name__ == "__main__":
    main()
