# Runtime acceptance — partial evidence; native interactions pending

Frozen Desktop LOADED is recorded in desktop-parent-check.json. Four saved Cloud
states and their data exports have been checked, with acceptable visual deltas.
Local SQL output models generated formulas; it does not execute actions. Real
browser interactions remain unavailable because the user cannot complete MFA.

1. Check SHA256 against handoff.json before opening the frozen artifact. Desktop must report LOADED; FAIL and UNKNOWN both fail acceptance. Do not rebuild after capturing evidence without refreshing hashes.
2. Open Filtering Table Calcs. Confirm 48 chronological months (Jan 2018–Dec 2021), area plus synchronized rolling-average line, and 17 sub-categories in two bar panels sorted by descending sales. Default total sales: 2,297,200.8603; average monthly total: 47,858.35125625. Check both parameters are dates, not subtraction expressions.
3. Drag June–September 2018 on Trend. Both parameters must change. June sales must be 34,595.1276; June rolling average must remain 28,846.2532. Bars must use these four months only and divide by 4. Compare all outputs to scenario zoom-jun-sep-2018 in local-verification.json.
4. Select just June. Its rolling average remains 28,846.2532 and the bar denominator becomes 1. Select Dec 2019–Feb 2020 to verify addressing crosses a year boundary correctly.
5. Clear the trend selection. Both date parameters must become 1900-01-01 and the full interval must return. Check that zoom can be repeated after clearing.
6. Select Chairs on Bars. Only Trend must filter, recomputing totals/averages across the full selected category history. Multi-select Chairs and Phones, then clear the bar selection. Compare category-chairs and multi-category scenarios. The bar panels retain all categories.
7. Saved Copiers and Machines REST exports have 32 and 39 observed months. Their
   sales and previous-two-observed-mark averages match the raw-data oracle and
   author Data sheet within display rounding. This does not exhaustively test
   dashboard densification. Both category REST filters directly affect Bars;
   these captures do not verify the native Bars-to-Trend action isolation.
8. Run Desktop corpus regression, Cloud validation and rendered author/replica comparison as scoped by the parent, then independent review. Record results without marking pending items as verified.

The integration agent regenerates the catalogue after parent authorization.
No browser action, Cloud/Desktop launch, push or PR was performed by that agent.
