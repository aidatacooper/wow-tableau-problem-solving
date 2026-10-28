# WW41: Top sub-category contribution

**Partial; visual delta accepted; real browser interactions pending.** The frozen
workbook rebuilds the Top N sales contribution question using cwtwb 0.29.0a1
(commit `23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`) and extracted raw Hyper data.
No SDK source was modified. See [analysis.md](analysis.md) for the business
question, construction boundary, numerical oracle and two released-SDK gaps.

## Current artifact and completed checks

- [Frozen workbook](outputs/replicated-workbook.twbx): SHA256
  `7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb`.
- [Parent Desktop check](evidence/desktop-parent-check.json): LOADED for that hash.
  [Regression corpus](evidence/desktop-corpus.json): 50 LOADED, 0 FAIL, 0 UNKNOWN.
- [Cloud render manifest](evidence/cloud-verification.json): author and replica
  PNGs at N=1,5,16,17. [CSV manifest](evidence/cloud-csv.json): 20 data exports.
- [Independent review](evidence/independent-final-review.md) and
  [hash binding](evidence/independent-final-review.json): no confirmed defects
  within four-state rendered/data/static scope. All 17 detail ranks, group
  subtotals and contribution values match an independent raw-row calculation.
- [Delivery validation](evidence/delivery-validation.json): final repository
  tests, metadata/provenance/public-API boundary, schema and disposable rebuild.
- [Case status](case.yaml), [artifact freeze](evidence/artifact-freeze.json) and
  [handoff](evidence/handoff.json) define the current partial result. Reports in
  `evidence/baseline-a1/` and original local reports describe earlier runs.

Visible contribution values are 14% (N=1), 56% (N=5), rounded 100% with a $3,024.28
remainder (N=16), and 100% with no remainder (N=17). Whole-dollar table labels
round the underlying data. The separate contribution heading, palette, fonts
and native subtotal positioning are accepted visual differences, not a pixel
match. Both pie angles use actual sales rather than the author's repeated LOD.

## Remaining acceptance

[Runtime scenarios](evidence/runtime-pending.md) require real dashboard pTopN
control changes and two-way Sales Group hover/auto-clear from pie and table,
including subtotal marks. Check unchanged totals and the excluded summary.
Browser MFA blocked those events. REST parameterized PNG/CSV requests are not
interactive parameter-control or hover evidence. Keep `functional_status:
partial` and `verification_status: pending` until actual events are recorded.

## Reproduce without overwriting frozen evidence

From the repository root in PowerShell, select the exact a1 SDK checkout:

```powershell
$env:PYTHONPATH='C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src'
$env:CWTWB_SRC=$env:PYTHONPATH
python -X utf8 scripts/validate_iteration.py iterations/2021-10-14-ww41-how-much-do-top-sub-categories-contribute-to-sales --metadata-only
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/validate_changed_cases.py --base-ref origin/main
python -X utf8 scripts/case_catalogue.py
```

The changed-case validator validates committed metadata, then builds, schema
checks and verifies a disposable copy. It preserves the frozen output and
captures. `build_replication.py` and `verify_replication.py` remain runnable for
new authoring, but direct execution rewrites output/evidence and requires new
hash-bound Desktop/Cloud evidence afterward. Credentials stay outside the repo.
