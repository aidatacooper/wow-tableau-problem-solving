# WW43 case progress

- [x] 2026-11-05 — Took over PR #25 at `c1abfb2` in isolated checkout and fetched `origin/main`.
- [x] 2026-11-05 — Merged `origin/main`; generated catalogue conflicts are being regenerated from `case.yaml`.
- [x] 2026-11-05 — Case verifiers, isolated validation, shared tests, and metadata-only validation passed without retaining a formal rebuild.
- [ ] 2026-11-05 — Push resolved branch and report the PAT REST capture checklist and IDs to parent.
- Remaining work: native drag/select/clear/repeated zoom/multi-select/reset and Bars-to-Trend action isolation require parent Cloud evidence; REST filter exports alone do not prove event isolation.
- [x] 2026-11-05 — `verify_replication.py` passed XSD, generated contracts, and 27 SQL/Decimal scenarios; Desktop/Cloud not run.
- [x] 2026-11-05 — `validate_iteration.py --metadata-only` passed with main requirements and preserved frozen artifact metadata.
- [x] 2026-11-05 — Updated the builder for required cwtwb 0.29.0a2 and replaced the tooltip EXACTDATE field with the supported bracketed date field; isolated rebuild and verifier passed, with frozen artifact unchanged.
- [x] 2026-11-05 — First shared test run reached 83 tests but two catalogue assertions failed because case metadata changed after the previous generation; regenerated catalogue is the corrective next step.
- [x] 2026-11-05 — Regenerated both catalogues after metadata changes; all 83 shared unittest cases pass.
- [x] 2026-11-05 — Post-restore verifier, saved-export verifier, and metadata-only validation pass; Desktop/Cloud not run.
