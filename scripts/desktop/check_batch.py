"""Check several workbooks in Tableau Desktop, one per line of output.

Usage:
    python scripts/desktop/check_batch.py <workbook> [<workbook> ...]

Prints a fixed-width verdict followed by the file name, so runs can be
diffed against the baseline in ``verify_corpus``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.desktop import verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbooks", type=Path, nargs="+")
    parser.add_argument("--tries", type=int, default=2)
    args = parser.parse_args()

    failed = False
    for workbook in args.workbooks:
        result = verdict.test_with_retries(os.path.abspath(workbook), tries=args.tries)
        print(f"{result:8s} {workbook.name}", flush=True)
        if result != verdict.LOADED:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
