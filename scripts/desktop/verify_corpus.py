"""Verify the Desktop-load regression baseline.

Opens every case in the baseline list and reports the aggregate verdict. This
is the regression gate for "Desktop can open the workbooks": a change to the
SDK or a builder must not drop a case that used to load.

Usage:
    python scripts/desktop/verify_corpus.py
    python scripts/desktop/verify_corpus.py --cases-file path/to/list.txt
    python scripts/desktop/verify_corpus.py --json out.json

Exit codes: 0 = all LOADED, 1 = at least one FAIL or UNKNOWN.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.desktop import verdict

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIST = REPO_ROOT / "scripts" / "desktop" / "desktop_baseline_cases.txt"
PRIMARY = "outputs/replicated-workbook.twbx"


def load_cases(path: Path) -> list[str]:
    """Read iteration directory names, ignoring blanks and comments."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-file", type=Path, default=DEFAULT_LIST)
    parser.add_argument("--tries", type=int, default=3)
    parser.add_argument("--json", type=Path, help="write the full result as JSON")
    args = parser.parse_args()

    cases = load_cases(args.cases_file)
    results: dict[str, str] = {}
    for name in cases:
        workbook = REPO_ROOT / "iterations" / name / PRIMARY
        if not workbook.is_file():
            results[name] = "NOBUILD"
            print(f"{'NOBUILD':8s} {name}", flush=True)
            continue
        result = verdict.test_with_retries(str(workbook), tries=max(1, args.tries))
        results[name] = result
        print(f"{result:8s} {name}", flush=True)

    loaded = [c for c, v in results.items() if v == verdict.LOADED]
    failed = [c for c, v in results.items() if v == verdict.FAIL]
    unknown = [c for c, v in results.items() if v == verdict.UNKNOWN]
    nobuild = [c for c, v in results.items() if v == "NOBUILD"]

    print(
        f"\nLOADED={len(loaded)} FAIL={len(failed)} "
        f"UNKNOWN={len(unknown)} NOBUILD={len(nobuild)}"
    )
    if failed:
        print("FAIL:", failed)
    if unknown:
        print("UNKNOWN (treat as failure):", unknown)
    if nobuild:
        print("NOBUILD:", nobuild)

    if args.json:
        args.json.write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.json}")

    return 0 if not (failed or unknown or nobuild) else 1


if __name__ == "__main__":
    sys.exit(main())
