# WW41 render correction, 2026-10-28

- Inspected the parent's actual Cloud PNG: inner pie label clipped at the right
  edge; subtotal rows displayed recalculated #1 and #2 rather than category ranks.
- Kept released cwtwb 0.29.0a1 at 23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c.
  No SDK change or candidate version is needed for these case-level corrections.
- Enlarged pies, centered inner labels, and introduced a rank prefix that checks
  the table-calculation partition against the FIXED category count. A subtotal
  partition has 1/2 group marks rather than the 17 detail marks, even for singleton
  groups. No numerical business values or hover behavior changed.
- Local verifier: all 17 raw-data scenarios and seven negative contract mutations
  pass, with XSD validity. Runtime effect remains pending until parent recaptures.
- The phase-boundary validator requires every TWB/TWBX to be directly in outputs/.
  Moved the unchanged original baseline workbook out of the parent's evidence
  archive into outputs/baseline-a1-workbook.twbx; retained SHA256 10c253f4751f7c9e3e583344c4366a0473271c4296e352dc634ebc0432a45f59.
- Next: parent serializes fresh Desktop and Cloud checks at N=1/5/16/17 and confirms
  label readability, rank removal on subtotals, and no category-rank regression.
- User cannot complete browser MFA now. Native parameter/hover interaction stays
  pending; REST parameter injection must not be described as actual interaction.

## Second correction round

- Parent Cloud verification rejected the first correction: the pie label remained
  outside the mark, and Rank Prefix's nested Sales Rank retained Rows addressing,
  displaying #1 for every category. Subtotal suppression did work.
- Replaced visible pie labels with a separate Contribution Summary heading above
  the pie, computed directly from conditional SUM(Sales) and FIXED total. It has
  no filters and is excluded from both hover source and target scopes.
- Added explicit Field/order addressing to the nested Sales Rank inside Rank
  Prefix, matching the outer context. Added negative checks for this actual
  failure and for re-enabling the clipped pie label.
- Current local checks: 17 numerical scenarios, eight rejected mutations, XSD.
  Parent Cloud review of default state confirms TOP 5 / 56% readable, ranks 1..17
  correct, and no false rank on subtotal rows. Parent retains N=1/16/17 and CSV
  acceptance, fresh Desktop, corpus, and independent review.
- Parent authorized refreshing generated indexes in this worktree; catalogue now
  contains 122 active cases (this isolated tree adds WW41 only).

- 2026-10-28 delivery integration: current frozen 7fa9c8916d33 verified against 8 PNG/20 CSV hashes, parent Desktop LOADED and 50 LOADED corpus. Independent review integrated; visual acceptable_delta, functional partial / verification pending for actual parameter UI + two-way hover/clear. 83 tests and disposable rebuild/XSD/verifier (17 states, 8 mutations) pass. Original branch snapshot precedes one-case origin/main isolation.

- 2026-10-28 one-case isolation: branch feat/2021-ww41-contribution-preview starts at origin/main d52ecab0449f7a0d443f22723fb59f7bd479649c. Restored only this case from original snapshot 61469ab; original t3 branch preserved. Catalogue now 112 active cases; 83 tests, metadata/boundary/source-lock, frozen XSD and disposable rebuild/verifier (17 scenarios, 8 mutations) pass. Frozen 7fa9c8916d33 unchanged; no Cloud/Desktop/push/PR executed during delivery integration.
