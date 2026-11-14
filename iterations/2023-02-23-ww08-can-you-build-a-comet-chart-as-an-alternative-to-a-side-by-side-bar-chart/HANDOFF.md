# Handoff commands

Run from the repository root in PowerShell. This worker changed only this iteration. No Desktop, SDK/index changes, commits, pushes or branch/worktree operations were performed.

```powershell
$case = 'iterations/2023-02-23-ww08-can-you-build-a-comet-chart-as-an-alternative-to-a-side-by-side-bar-chart'
$env:CWTWB_SRC = 'C:/Users/imgwho/Desktop/project/cwtwb/src'
$env:PYTHONPATH = $env:CWTWB_SRC
$env:PYTHONIOENCODING = 'utf-8'
python scripts/desktop/sdk_source.py --expect cwtwb
python "$case/build_replication.py"
python "$case/verify_replication.py"
python scripts/validate_iteration.py $case
python -m unittest discover -s tests -v
```

The last two commands were executed. Case-specific checks passed; full validator and two of 83 repository tests failed only because the shared generated catalogue is stale. Parent must regenerate it from final metadata (`python scripts/case_catalogue.py --write`) and rerun both. This worker intentionally did not write it.

To repeat source provenance, builder and verifier together:

```powershell
python "$case/run_checks.py" --channel final --validate
```

This records the full validator exit code; a catalogue-only integration failure is marked deferred separately from SDK construction success. To reproduce stable baseline in a fresh checkout, install the exact stable package under the ignored runtime directory and download the wheel specified by evidence/pypi.json, or use a clean package environment. The recorded stable-run.json contains the actual import path and verified wheel SHA256. On this machine run_checks restores the preserved inactive package before a stable run and deactivates it afterward so the repository's recursive builder scan does not scan SDK implementation:

```powershell
python "$case/run_checks.py" --channel stable
# Always restore the selected final source artifact afterward:
python "$case/run_checks.py" --channel final --validate
```

Parent-only serialized Desktop commands (not executed here):

```powershell
python scripts/desktop/build_and_check.py $case --sdk-src $env:CWTWB_SRC
python scripts/desktop/verify_corpus.py
```

Complete all four manual acceptance IDs using evidence/desktop-acceptance.md, capture the screenshot/export/interaction observations with final workbook hash, then update case status and indexes. A rebuild after evidence capture invalidates prior hash-bound evidence. Functional status is partial until these steps pass.

Final tested SDK: 0.29.0a3, clean Git commit 2b72232245959934281c49308f5c3b2fca8fc519. Source-tree SHA256: 491d5979516636ea43779ed3205aed724c9e19e4f4f1c3558c2877ff43910d8c.
Final worker artifact SHA256: 12de2b73af882615fa055a41d01005744680c4cde415b06f71d46b844937f2ea.
