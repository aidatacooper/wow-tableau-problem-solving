# Remaining live event gates — PENDING

Current frozen SHA256: `07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd`.

Completed: independent numerical/visual review of three current Cloud REST states, nine current-hash CSV exports, exact-hash Desktop LOADED (`desktop-parent-check.json`), and Desktop corpus LOADED=50 FAIL=0 UNKNOWN=0 (`desktop-corpus.json`). Desktop/Cloud actions were performed by the parent; this delivery only inspected supplied evidence.

1. Click Month, Quarter, Year, and Month again; compare the eleven categories and seven-member mean with local-verification.json.
2. Clear each selection and confirm the selected period persists.
3. Inspect selecting multiple distinct KPI marks; ATTR must not assign an arbitrary valid period.
4. Hover on marks and verify tooltips are absent; inspect selection highlighting during actual selection.

Browser MFA was not completed. REST parameter injection does not prove these events. Keep functional_status partial solely while these live event checks are open.

## PAT REST capture checklist for the parent

- Use Tableau Cloud REST with the existing PAT; do not use browser login or claim browser hover/select/drag/clear.
- Capture author workbook `70dc1b8b-19aa-4daa-a32d-426509bf4713`, view `d46c7d95-6b21-4a1e-a99a-a7b7ce77bc8d`, and replica workbook `5834782f-b44a-479d-8cfe-15d83a2e577c`.
- Capture replica views `Period KPIs` (`a2561b8e-7b96-411f-bbfe-51aae8663a19`), `Profit Performers` (`1d3639de-6385-4617-aa46-a80a97d78aad`), and `WW44 Profit Performers` (`a0c499a4-319e-42de-a465-d73ab27f41be`).
- Request `default`, `quarter` (`pDatePart=Quarter`, `Period=Quarter`), and `year` (`pDatePart=Year`, `Period=Year`) for both PNG and worksheet CSV data. Record source artifact SHA256, response file SHA256/bytes, parameters, view IDs, and `browser_interaction_executed: false`.
- Run `python -X utf8 verify_rest_contract.py --cloud <cloud-verification.json> --csv <cloud-csv.json>` against the capture directory. A failed hash, ID, state, dimension, or byte check is a failed contract; do not promote `functional_status`.
