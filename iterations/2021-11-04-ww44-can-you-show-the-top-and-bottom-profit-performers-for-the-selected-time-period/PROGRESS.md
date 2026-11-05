# WW44 progress

- [x] 2026-11-05 — Reset checkout to PR #24 head `214bbc8`, merged `origin/main`, and regenerated `usage/case-index.json` plus `usage/consumed-cases.json` from case metadata.
- [x] 2026-11-05 — Confirmed frozen `outputs/replicated-workbook.twbx` SHA256 `07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd`; no accepted TWBX/PNG/CSV bytes were rebuilt or changed.
- [x] 2026-11-05 — Ran `verify_replication.py` under installed `cwtwb 0.29.0a2`: 8 local contracts, 3 numerical period scenarios, 3 mutation checks passed.
- [x] 2026-11-05 — Added and ran `verify_rest_contract.py`; current PAT REST manifests pass 3 image states, 9 CSV records, artifact hash, workbook/view IDs, PNG dimensions, and explicit `browser_interaction_executed: false` checks.
- [x] 2026-11-05 — Recorded current Cloud IDs for parent capture: author workbook `70dc1b8b-19aa-4daa-a32d-426509bf4713`, author view `d46c7d95-6b21-4a1e-a99a-a7b7ce77bc8d`; replica workbook `5834782f-b44a-479d-8cfe-15d83a2e577c`; views `Period KPIs` `a2561b8e-7b96-411f-bbfe-51aae8663a19`, `Profit Performers` `1d3639de-6385-4617-aa46-a80a97d78aad`, `WW44 Profit Performers` `a0c499a4-319e-42de-a465-d73ab27f41be`.
- [ ] Remaining — PAT REST can establish static Month/Quarter/Year image/data states and artifact hashes. A browser session is still required for real KPI click, clear retention, multi-select ATTR behavior, and hover/selection highlighting; these remain outside accepted scope and `functional_status` stays `partial`.
