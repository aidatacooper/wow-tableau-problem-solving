# WW44 — Top and bottom profit performers

The current frozen workbook rebuilds the latest-calendar Month, Quarter and Year profit comparison with native top/bottom-five sets and a seven-category middle average.

- `functional_status: partial`: exact-hash Desktop LOADED and the 50-case corpus pass; real clicks, clear selection, multi-selection and hover remain pending.
- `visual_status: acceptable_delta`: the current three Cloud REST states have readable KPIs and all eleven category/value labels; independent raw-data SQL agrees with their figures. Palette, typography and spacing differ from the author.
- `cwtwb_result: pass`, current verifier tested against installed `cwtwb 0.29.0a2`; the historical a1 build records remain append-only.
- Frozen `outputs/replicated-workbook.twbx` SHA256: `07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd`.

Read [analysis](analysis.md), [independent review](evidence/independent-review.md), [review hash binding](evidence/independent-review.json), [Cloud capture manifest](evidence/cloud-verification.json), [local gates](evidence/local-gates.json), and [handoff](evidence/handoff.json). Historical baseline evidence is under `evidence/baseline-a1`; its frozen workbook is `outputs/baseline-a1-replicated-workbook.twbx`.

Set `PYTHONPATH` and `CWTWB_SRC` to `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`, with `PYTHONUTF8=1`. The builder and verifier are runnable with `python -X utf8 <case>/build_replication.py` and `verify_replication.py`. A build replaces the workbook and requires a new freeze and runtime evidence. To validate the delivered package without replacing it, run metadata-only validation on this case and execute full `validate_iteration.py` against an isolated copy of the case. The final delivery gate did this; details and commands are in `evidence/local-gates.json`.

REST parameter injection is evidence for each rendered state. `verify_rest_contract.py` checks the current workbook hash, PAT REST image/data manifests, all three period states, nine CSV hashes, PNG dimensions, and current workbook/view IDs. It does not establish live KPI clicks, clear-selection retention, multi-selection or tooltip hover; those events remain pending. Parent evidence records exact-hash Desktop LOADED and corpus LOADED=50 FAIL=0 UNKNOWN=0. Current `cloud-csv.json` binds all nine REST exports to the frozen package; their file hashes pass.
