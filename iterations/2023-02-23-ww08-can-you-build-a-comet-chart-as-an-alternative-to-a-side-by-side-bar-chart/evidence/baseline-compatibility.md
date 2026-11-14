# Old repository-pin compatibility — 2026-11-14

Interpreter: `../case-2024/.venv/Scripts/python.exe`. Installed SDK: `0.29.0a2`, Git pin `cac8820f26e703c3858253adfa21efd989eb8a78`, matching unchanged repository requirements. `CWTWB_SRC` and `PYTHONPATH` were absent; `PYTHONUTF8=1`.

- `python -m unittest discover -s tests -v`: PASS, 83 tests in 13.450 seconds. Full output: `baseline-unittests.log.txt`.
- `python scripts/case_catalogue.py --write`: PASS, 146 active cases.
- `python scripts/validate_changed_cases.py --base-ref origin/main`: PASS against committed case `2a3c1884845804e6450f843b5d01ca26669c184a`. Full output: `baseline-changed-cases.log.txt`. The validator rebuilt and verified the case in its disposable temporary copy; the accepted primary workbook was not rebuilt.
- Committed builder, verifier and TWBX bytes match all three hashes in `desktop-final-fit-20261114.json`. Primary TWBX remains `6438345df80931b943bae5115d13783b6a714a8f381aabd29f5596abab6ee2cb`.
- Both copied corpus JSON files match the shared source bytes exactly.

The visual metadata initially lacked required screenshot links. Canonical `outputs/cloud-author.png` and `outputs/cloud-replica.png` are exact copies of the existing reference and Desktop screenshot. Their schema names do not imply Cloud captures. The final changed-case run passes after that metadata correction.

These old-pin automated checks do not establish Desktop behavior or fit equivalence for the old SDK. The accepted Desktop artifact uses SDK `056050c8e95f5fbe3560886e566c34aee53b40b0`. The 50-case Desktop corpus remains PRE-FIX release evidence.

Final Desktop screenshot SHA256: `c9ce41d8c540dc9e285cc279b39f5832981f9cc33420d72826d9d8d660057cb6`.

Author reference SHA256: `e689b8fe050e8cc62151e1949264b100a5cd06c9e165a003283c15eee88d0196`.
