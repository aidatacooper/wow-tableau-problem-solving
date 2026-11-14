# Parent handoff: 2025 Week 2 Visualizing Ranges

## Accepted Desktop artifact and release submission

Parent completed real Desktop LOADED, dashboard/reference comparison, Hour 15 P75 hover at 162.0, and Copy > Crosstab verification of all 168 displayed values over 24 hours. The evidence hashes match the unchanged primary artifact `fc29870d0ac45a7615fa0d599c01d38de925a28fa349aa43ea3e9df54e565a6c`. `evidence/desktop-accepted-20261114.json` binds the acceptance records, actual TSV and screenshots. Metadata is replicated / acceptable_delta / verified. Typography and direct-label differences are accepted; the legacy Cloud-named image slots refer to local article/Desktop images.

requirements.txt pins merged SDK PR25 `bbd749f25a5375889a66a8cd72aaaee129810353`, matching workflow PR65. Validation uses an isolated exact-pin environment and `validate_changed_cases.py --base-ref origin/main`, which rebuilds in disposable copies only. The accepted primary is never rebuilt. The previous freeze and partial-status notes below are historical.

The post-fix full Desktop corpus remains parent-owned and pending; copied 50-LOADED corpus evidence is pre-fix only. No new Desktop execution or SDK edits are performed by this integration.

## Current handoff — manifest fix, 2026-11-14

The artifact is frozen for parent-owned Desktop and rendered acceptance:
`outputs/replicated-workbook.twbx`
SHA256 `fc29870d0ac45a7615fa0d599c01d38de925a28fa349aa43ea3e9df54e565a6c`.
Clean SDK `056050c8e95f5fbe3560886e566c34aee53b40b0`, version `0.29.0a3`, explicit CWTWB_SRC/PYTHONPATH `C:/Users/imgwho/Desktop/project/cwtwb/src`.
Python source fingerprint `4f295e834bf64674764ef9665c8de962b4e3d87c90125342e72466d0ae50ec9e`.

The full validator (including rebuild, XSD, boundary, metadata, identity, catalogue and case verifier) passes; all 83 shared tests pass. The verifier requires PatternedLineMarks and rejects an in-memory copy with that flag removed. All 168 numerical comparisons pass. New append-only records: `evidence/manifest-fix-20261114.json`, `evidence/manifest-fix-static-20261114.json`, `evidence/manifest-fix-validated-verification-20261114.json`, and `evidence/manifest-fix-freeze-20261114.json`. The full validator rebuilt the artifact, so its final hash above supersedes the first manifest-fix run's hash.

The previous Desktop FAIL D2E8DA72 remains in `evidence/desktop-failed-pattern-20261114.json`. Its cause is the generic missing PatternedLineMarks manifest fixed upstream in SDK PR25; the original mark-line-pattern attribute remains correct and unchanged. No SDK edits were made here.

Copied `evidence/desktop-corpus*.json` describe the pre-fix SDK `2b72232245959934281c49308f5c3b2fca8fc519`, with 50 LOADED. They do not prove full regression of the fixed SDK; `evidence/corpus-scope-20261114.json` records this limitation.

Parent: open the frozen artifact directly for UI verification. Rebuilding changes its hash and requires fresh evidence. The non-UI owner has stopped writing after this freeze; no Desktop activity, commit, push or SDK change was performed. Status remains partial/not_evaluated. Remaining gates are the Desktop load, rendered comparison of all 24 hourly oracle rows, median/area/label/reference-line acceptance, screenshot, and current-source corpus regression. Shared indexes in this clone have been regenerated.

## Historical handoff below — superseded, not current execution instructions

All writes are inside iterations/2025-01-14-ww02-visualising-ranges. No Desktop activity, commits, index updates, SDK edits, worktree or branch changes. Fresh origin/main at claim was e32c8151a8c596c082763007d2ec5fc83cf1ddff; active iteration tree and open issues checked.

## Commands from repository root

```powershell
$case = 'iterations/2025-01-14-ww02-visualising-ranges'
$env:CWTWB_SRC = 'C:/Users/imgwho/Desktop/project/cwtwb/src'
$env:PYTHONPATH = $env:CWTWB_SRC
$env:PYTHONIOENCODING = 'utf-8'
python "$case/build_replication.py"
python "$case/verify_replication.py"
python "$case/check_static.py"
python scripts/validate_iteration.py $case
python -m unittest discover -s tests -v
```

Builder/verifier and case-local metadata, source-lock, public SDK boundary and XSD PASS. Native percentiles remain in workbook; independent Python sorted interpolation vs Hyper SQL passes all 168 min/percentile/max values over 4319 rows / 24 hourly groups. The full validator passes case gates but stops at stale shared usage/case-index.json. Shared suite: 83 tests, 81 pass, 2 catalogue-only failures (test_prepare_case_extracts_data_and_never_copies_source; test_validator_scans_helper_files_and_rejects_misplaced_workbooks), logged in evidence/shared-tests.txt. Parent should regenerate indexes before repeating full validator/shared tests.

## Stable baseline command

```powershell
Remove-Item Env:CWTWB_SRC -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
uv run --isolated --with cwtwb==0.28.0 --with tableauhyperapi python iterations/2025-01-14-ww02-visualising-ranges/record_run.py pypi-stable-RETEST
```

Use a NEW run label rather than overwrite evidence; append actual result to case.yaml cwtwb.runs. This builds and changes the output; restore selected source and retest before Desktop. Stable 0.28.0's wheel SHA advertised by PyPI is dd8fb1c4a7a1828ba6c102afa5bc13f90dc7c959c58cde608d2de0a830a05225. The initial missing tableauhyperapi dependency failure is preserved separately and not classified as an SDK gap.

## Final tested selected source
Version 0.29.0a3; full clean SHA 2b72232245959934281c49308f5c3b2fca8fc519; import C:/Users/imgwho/Desktop/project/cwtwb/src/cwtwb/__init__.py. Python source tree fingerprint 63164f5aedf70c74c7d89af0b0e82dfaab0786ef87f74b804f72f981f083fd84. Final run evidence: evidence/selected-source-final.json. No SDK gap.

Final handed-off TWBX SHA256: fa3c13798f7b9002b3db3d2d5476504017caee750f3ef21ef8c9936fb2bd0318.

## Remaining parent-only gates

```powershell
$env:CWTWB_SRC = 'C:/Users/imgwho/Desktop/project/cwtwb/src'
$env:PYTHONPATH = $env:CWTWB_SRC
python scripts/desktop/build_and_check.py iterations/2025-01-14-ww02-visualising-ranges --sdk-src $env:CWTWB_SRC
python scripts/desktop/verify_corpus.py
```

Follow evidence/desktop-acceptance.md: LOADED, actual rendered numeric values against all 24 hourly oracle rows, median visibility, six areas correctly layered and labeled, dotted 80/180 boundaries, 1300x600 single worksheet. Standard hover only; original challenge requires no selector or reset actions. The author's local archive PNG is only a loading placeholder; use evidence/article-reference.png as the inspected reference.

After every rebuild, rebind actual hash evidence. Complete Desktop/visual acceptance and final SDK runs, update metadata honestly, regenerate shared indexes with python scripts/case_catalogue.py --write, rerun full validator and shared suite, then parent commits/pushes per case. Metadata intentionally remains partial/not_evaluated until observed acceptance passes.
