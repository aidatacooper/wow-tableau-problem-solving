# WW43 acceptance integration, 2026-10-28

- Kept frozen workbook 83893921f3dbaa372e88baa3a82f3027e352f1828ddbab242d63efa10fedc379
  unchanged, using released cwtwb a1 at 23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c.
- Preserved supplied independent review and all its objections; this integration
  is not a fresh independent review. SDK run-spec finding belongs to separate SDK work.
- Added reproducible saved-export verification covering four states and all CSV/
  PNG hashes. Machines has 39 observed months and matches raw oracle/author Data;
  default/June/Copiers have 48/1/32. No exhaustive densification or action claim.
- Inspected four replica images plus author default/Machines: acceptable_delta;
  functional partial. REST category filters also filter Bars, unlike native action.
- Full isolated rebuild, schema and 27-scenario/six-mutation verifier pass without
  changing accepted bytes. Metadata/catalogue validation passes. 83/83 tests pass.
- Parent completed fresh Desktop LOADED and corpus LOADED=50 FAIL=0 UNKNOWN=0.
- Added local attributes to preserve binary/captured CSV/review bytes in Git.
- Next: parent restores only this case onto origin/main, regenerates catalogues
  there, and opens its own PR. Original t3 branch retained, no rebase/push/PR here.
- Remaining acceptance: actual drag/min-max/clear/repeated zoom/multi-select/reset
  and native action isolation after user MFA. Saved REST data cannot prove these.

## Main-base delivery branch

- Retained t3/ww43-filtering-table-calcs at f80d75baa1c58fef874a275130a0bcf401a3d2be.
- Switched the existing clean worktree to feat/2021-ww43-table-calc-preview from
  origin/main d52ecab0449f7a0d443f22723fb59f7bd479649c; restored only this case.
- Regenerated indexes from main's 111 cases plus WW43: 112 active cases. No old
  generated view or unrelated unpublished case was restored.
- Re-ran all 83 repository tests and isolated full build/schema/verifier plus
  metadata/boundary/source-lock/identity/catalogue checks on this main base.
  Accepted frozen workbook hash remained unchanged.
