# WW49 local implementation handoff

Local implementation is complete; functional status remains **partial**, visual
**not_evaluated**, verification **pending** until parent runtime acceptance.
SDK result is **workaround** for documented data-grain preprocessing, not an SDK
blocker. No SDK changes, Desktop, Cloud, browser, live-event, push or PR actions.

## Source and frozen identity

- Worktree: `C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-ec9ee22b`
- Branch: `t3/ww49-frequency-matrix-case`
- Clean starting origin/main: `d52ecab0449f7a0d443f22723fb59f7bd479649c`.
- Final source commit: the commit containing this handoff (`git rev-parse HEAD`).
  Exact builder/verifier/analysis hashes are in `evidence/frozen-manifest.json`.
- Tested published SDK: `0.29.0a2`, tag commit
  `7e7731e474ceab5678fa64b681f16402fb90f57a`; no merged-cac8820 retest was needed.
- Primary frozen workbook: `outputs/replicated-workbook.twbx`.
- Primary SHA256: `822ce8440be214d935bc34a1bf6106c9840d4a72954406e9834be5a12b31eeb2`.
- Author archive SHA256 remains
  `13fbad267c5951a30ed56ad45a6698fa7bacab3e281c36142e5573221cf07708`.
- Extracted raw Hyper SHA256 remains
  `cdb3dde88490f0efa12e9a4834d9be74b330ce95cc6942356d0aa6fbb8f30a6e`.
- `outputs/role-probe.twbx` is a declared historical probe, superseded after
  correcting Triangle to a table-calculated nominal measure/User instance.
  Do not open it as the acceptance artifact. It is checked only by `--frozen`;
  the fresh verifier does not require historical archives cleared by CI.
- Root requirements pin changed from older Git 0.29.0a1 to published 0.29.0a2
  for CI reproducibility. No global install was changed.

## Exact local commands and results

Run in the worktree, PowerShell:

```powershell
$env:PYTHONPATH='C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving/scratch/sdk-release-0.29.0a2'
$env:CWTWB_SRC=$env:PYTHONPATH
$case='iterations/2021-12-12-ww49-which-sub-categories-are-frequently-ordered-together'
python scripts/case_catalogue.py --write
python scripts/validate_iteration.py $case
python -m unittest discover -s tests -v
python "$case/verify_replication.py" --frozen
```

Before freezing, `validate_iteration.py` passed source lock, metadata, phase
boundary, builder, strict XSD and verifier. All 83 repository tests passed (see
`evidence/local-tests.txt`). Oracle checked 306 cells (153 visible), 20 synthetic
cells, all actual order memberships and both sales contributions; all 19
negative mutations were rejected. JSON cell-level values are in
`outputs/verification.json`. The source article/official date identify December
8, 2021, not the historical 2018 Tableau link selected by the intake bug.

A final isolated rebuild passed after copied TWB/TWBX outputs were deleted,
including the historical probe. Use this after freeze to avoid replacing the
accepted artifact with new random UUIDs:

```powershell
python -c "from pathlib import Path; from scripts.validate_iteration import run_case_scripts_isolated; run_case_scripts_isolated(Path('iterations/2021-12-12-ww49-which-sub-categories-are-frequently-ordered-together').resolve())"
python "$case/verify_replication.py" --frozen
```

The build-provenance JSON binds its actual imported distribution/module and
output hash; no local SDK Git checkout is required. For another machine install
`requirements.txt` into its own environment. Set PYTHONPATH/CWTWB_SRC only to
that environment's actual package root, not to this workstation's path.

## Parent runtime gates and concrete expectations

1. Open the frozen primary with the Desktop log gate; require **LOADED**.
   `python scripts/desktop/check.py "$case/outputs/replicated-workbook.twbx"`
   If using `build_and_check.py`, always pass `--sdk-src` explicitly and do so in
   an isolated copy: that command rebuilds and would invalidate frozen hashes.
2. Confirm one worksheet, 1100 x 900 dashboard, NONE then alphabetical columns,
   alphabetical rows, 153 lower-triangle cells, no diagonal, white upper half,
   readable rotated labels, white dividers and ColorBrewer BuPu square colors.
   Fixed mark size/scaling is contract checked; actual square fill needs render.
3. Hover ACCESSORIES/NONE: **196 orders**, **$207.14** row average; singular
   SUB-CATEGORY, no second title/label/colon/value. Duplicate same-category lines
   must not exclude an order from NONE.
4. Hover BINDERS/ACCESSORIES: **161 orders**, BINDERS **$174.59**, ACCESSORIES
   **$187.08**. Plural SUB-CATEGORIES, both titles and colons. Hidden reciprocal
   ACCESSORIES/BINDERS has the same count and swapped contributions in the data.
5. Hover CHAIRS/BOOKCASES: **21 orders**, CHAIRS **$553.52**, BOOKCASES **$688.55**.
   Verify actual dollar format, not just XML syntax. Check native selection and
   clearing do not filter or re-index categories. There are no author dashboard
   actions, user category filters, parameter controls or color legend to mimic.
6. Run parent-serialized corpus regression and independent different-model
   review. Cloud/capture or live events require parent's available credentials;
   no live events are claimed here. Mark all failed/unknown runtime checks as
   unresolved, not passed. Update functional/visual status only from evidence.
7. Parent owns any final runtime fixes, refreshed evidence, push and PR. Preserve
   the baseline run record and append new SDK runs if retesting another release.

No external/capability blocker is demonstrated. Remaining work is exclusively
runtime acceptance and independent review, not an unfinished local builder.

## Parent header fix

Current frozen SHA: `09708672f5f140fb57f4d07d335c65610d8a5ff9a201378050a11ba508849dde`. Public header sizing fixes independently reported clipping; actual Cloud PNG inspected and full labels visible. Current Desktop LOADED and local verifier passes. Historical baseline and all original evidence preserved under outputs/baseline-822ce844.twbx and evidence/archive-822ce844. Current runtime evidence is in evidence/cloud-verification.json. Final independent visual recheck, corpus and live interactions remain pending.

Final parent gates: current-artifact Desktop LOADED; corpus LOADED=50 FAIL=0 UNKNOWN=0 NOBUILD=0 (evidence/desktop-corpus.json); final independent visual recheck approved. Live hover/selection/clearing unverified; draft PR remains partial.
