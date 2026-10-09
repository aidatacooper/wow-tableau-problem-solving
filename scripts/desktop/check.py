"""Check one workbook in Tableau Desktop.

Usage:
    python scripts/desktop/check.py <workbook> [tries]

Exit codes: 0 = LOADED, 1 = FAIL, 2 = UNKNOWN after every try.
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
    parser.add_argument("workbook", type=Path)
    parser.add_argument("tries", type=int, nargs="?", default=3)
    args = parser.parse_args()

    path = os.path.abspath(args.workbook)
    for attempt in range(1, max(1, args.tries) + 1):
        result = verdict.test_with_retries(path, tries=1)
        print(f"try{attempt}: {result}", flush=True)
        if result != verdict.UNKNOWN:
            return 0 if result == verdict.LOADED else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
