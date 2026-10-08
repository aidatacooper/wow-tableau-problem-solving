"""Rebuild a case with a chosen ``cwtwb`` checkout, then check it in Desktop.

This is the cross-repository loop: edit the SDK, rebuild an affected case
against that SDK, and confirm Tableau Desktop still opens the result. It
fails loudly when the SDK actually imported is not the one requested, because
that mistake otherwise looks like "the SDK change had no effect".

Usage:
    # Use the ambient editable cwtwb install.
    python scripts/desktop/build_and_check.py <case-dir>

    # Use a cwtwb worktree, and refuse to continue if it is not the one loaded.
    python scripts/desktop/build_and_check.py <case-dir> --sdk-src <cwtwb-wt>/src

    # Rebuild every case in a list file and check each one.
    python scripts/desktop/build_and_check.py --cases-file cases.txt --sdk-src ...

Exit codes: 0 = every case built and loaded, 1 = a failure, 2 = usage error.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.desktop import sdk_source, verdict

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIMARY = "outputs/replicated-workbook.twbx"


def build(case_dir: Path, sdk_src: str | None) -> tuple[int, str]:
    """Run the case builder, returning its exit code and combined output."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    if sdk_src:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = sdk_src + (os.pathsep + existing if existing else "")
        env[sdk_source.ENV_VAR] = sdk_src
    proc = subprocess.run(
        [sys.executable, "build_replication.py"],
        cwd=case_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def primary_workbook(case_dir: Path) -> Path:
    """Return the case's primary workbook path."""
    import yaml

    metadata = case_dir / "case.yaml"
    relative = DEFAULT_PRIMARY
    if metadata.is_file():
        document = yaml.safe_load(metadata.read_text(encoding="utf-8")) or {}
        relative = (
            document.get("artifacts", {}).get("primary_workbook") or DEFAULT_PRIMARY
        )
    return case_dir / relative


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, nargs="?")
    parser.add_argument(
        "--cases-file",
        type=Path,
        help="file with one iteration directory name per line",
    )
    parser.add_argument(
        "--sdk-src",
        help="path to a cwtwb checkout (its root or its src directory)",
    )
    parser.add_argument(
        "--tries",
        type=int,
        default=2,
        help="Desktop attempts per workbook before reporting UNKNOWN",
    )
    parser.add_argument(
        "--skip-desktop",
        action="store_true",
        help="only rebuild; do not open Tableau",
    )
    args = parser.parse_args()

    if bool(args.case_dir) == bool(args.cases_file):
        parser.error("pass exactly one of case_dir or --cases-file")

    if args.sdk_src:
        os.environ[sdk_source.ENV_VAR] = args.sdk_src
    active = sdk_source.active_cwtwb()
    print(
        f"SDK: {active['sdk_root']} "
        f"(version {active['version']}, via {active['selected_by']})",
        flush=True,
    )
    if args.sdk_src:
        requested = Path(os.path.expandvars(args.sdk_src)).resolve()
        if requested.name != "src":
            requested = requested / "src"
        actual = Path(active["sdk_root"] or "").resolve()
        if requested != actual:
            print(
                f"ERROR: requested SDK {requested} but {actual} is active",
                file=sys.stderr,
            )
            return 1

    if args.cases_file:
        names = [
            line.strip()
            for line in args.cases_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        cases = [REPO_ROOT / "iterations" / name for name in names]
    else:
        cases = [args.case_dir]

    failures: list[str] = []
    for case_dir in cases:
        case_dir = case_dir.resolve()
        if not (case_dir / "build_replication.py").is_file():
            print(f"NOBUILD  {case_dir.name}: no build_replication.py")
            failures.append(case_dir.name)
            continue
        code, output = build(case_dir, active["sdk_root"])
        if code != 0:
            tail = "\n".join(output.strip().splitlines()[-8:])
            print(f"BUILDFAIL {case_dir.name}\n{tail}")
            failures.append(case_dir.name)
            continue
        if args.skip_desktop:
            print(f"BUILT    {case_dir.name}")
            continue
        workbook = primary_workbook(case_dir)
        if not workbook.is_file():
            print(f"NOARTIFACT {case_dir.name}: {workbook}")
            failures.append(case_dir.name)
            continue
        result = verdict.test_with_retries(
            str(workbook), tries=max(1, args.tries)
        )
        print(f"{result:8s} {case_dir.name}", flush=True)
        if result != verdict.LOADED:
            failures.append(case_dir.name)

    if failures:
        print(f"\n{len(failures)} failed: {', '.join(failures)}")
        return 1
    print(f"\nall {len(cases)} cases built and loaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
