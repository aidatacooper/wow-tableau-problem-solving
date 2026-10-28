# WW44 — Top and bottom profit performers

The current frozen workbook rebuilds the latest-calendar Month, Quarter and Year profit comparison with native top/bottom-five sets and a seven-category middle average.

- `functional_status: partial`: exact-hash Desktop LOADED and the 50-case corpus pass; real clicks, clear selection, multi-selection and hover remain pending.
- `visual_status: acceptable_delta`: the current three Cloud REST states have readable KPIs and all eleven category/value labels; independent raw-data SQL agrees with their figures. Palette, typography and spacing differ from the author.
- `cwtwb_result: pass`, tested `0.29.0a1`, commit `23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`.
- Frozen `outputs/replicated-workbook.twbx` SHA256: `07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd`.

Read [analysis](analysis.md), [independent review](evidence/independent-review.md), [review hash binding](evidence/independent-review.json), [Cloud capture manifest](evidence/cloud-verification.json), [local gates](evidence/local-gates.json), and [handoff](evidence/handoff.json). Historical baseline evidence is under `evidence/baseline-a1`; its frozen workbook is `outputs/baseline-a1-replicated-workbook.twbx`.

Set `PYTHONPATH` and `CWTWB_SRC` to `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`, with `PYTHONUTF8=1`. The builder and verifier are runnable with `python -X utf8 <case>/build_replication.py` and `verify_replication.py`. A build replaces the workbook and requires a new freeze and runtime evidence. To validate the delivered package without replacing it, run metadata-only validation on this case and execute full `validate_iteration.py` against an isolated copy of the case. The final delivery gate did this; details and commands are in `evidence/local-gates.json`.

REST parameter injection is evidence for each rendered state. It does not establish that live KPI clicks, clear-selection retention, multi-selection or tooltip hover work. Only those live events remain pending. Parent evidence now records exact-hash Desktop LOADED and corpus LOADED=50 FAIL=0 UNKNOWN=0. Current `cloud-csv.json` binds all nine REST exports to the frozen package; their file hashes pass. No push or PR is part of this delivery.
