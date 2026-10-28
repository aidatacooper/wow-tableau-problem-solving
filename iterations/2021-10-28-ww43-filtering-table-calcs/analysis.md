# Filtering Table Calcs — WoW 2021 W43

## Business question and identity

Compare monthly sales with a trailing three-observation monthly average, zoom into a selected date interval without resetting that average, and inspect a selected sub-category. The accompanying two bar panels show total sales and average monthly sales for the selected date interval, sorted by total sales descending.

- Article: https://donnacoles.home.blog/2021/10/28/filtering-table-calcs/ (2021-10-28).
- Official challenge: https://www.workout-wednesday.com/wow2021w43tab/ (2021-10-26; WordPress record 6176).
- Canonical identity: `wow-2021-ww43-filtering-table-calcs`.
- Folder: `2021-10-28-ww43-filtering-table-calcs` retains the article date.
- `case_intake.py` matched the correct workbook/year/week but picked a 2026 search candidate's date/URL. This case explicitly uses the matching 2021 W43 candidate. No shared intake code was changed.
- Author workbook URL and original archive SHA256 are in `case.yaml` and `inputs/source-lock.json`.

## Analysis-only observations

The archived author TWBX was inspected directly in the original repository during analysis, without copying its XML into this case. `prepare_case` extracted its packaged data once. The workbook contains a Trend-like sheet called Chart, a Bars sheet and a development crosstab called Data. Only the first two are needed for the dashboard.

The packaged CSV is UTF-16 tab-delimited despite its `.csv` extension. Both data representations contain 9,994 orders/line items, 17 sub-categories, and 48 distinct months from January 2018 through December 2021. Total sales are 2,297,200.8603. The Hyper table is `Extract.Extract`; dates are native date columns and Sales is a double. The builder connects to that extracted table. The independent numerical oracle reads the CSV with Python `Decimal`; a separate SQL implementation operates on the Hyper extracted from the generated TWBX.

Author calculations use monthly-truncated dates, two date parameters defaulting to 1900-01-01, FIXED minimum/maximum dates as fallback, a row-level inclusive date predicate, a zero-offset LOOKUP of that predicate, and a count of calendar months inclusive of both endpoints. The author trend's quick moving-average calculation has bounds -2 through 0 and average aggregation. Its table calculations use Rows ordering; the development crosstab demonstrates explicit date addressing. The author has two parameter actions aggregating selected dates by min/max and resetting to the sentinel on clear, plus a Bars-to-Chart sub-category filter action.

## Independent construction and filter order

`build_replication.py` starts with `TWBEditor("")`, connects only to the extracted Hyper, and uses public APIs for every field, worksheet, style and action. It never imports or copies the author workbook, XML, cached results, or layout.

1. `Order Date Month = DATE(DATETRUNC('month',[Order Date]))`.
2. `pMinDate` and `pMaxDate` initially hold Tableau date literal `#1900-01-01#`.
3. Selected endpoints use the parameter, or the FIXED global data minimum/maximum while the parameter is the sentinel.
4. `Is Month Selected?` is the inclusive row-level comparison to those endpoints.
5. `Visible Month = LOOKUP(MIN([Is Month Selected?]),0)` is a boolean table calculation.
6. `Rolling Average = WINDOW_AVG(SUM([Sales]),-2,0)` runs on the entire current monthly series.
7. The trend filters `Visible Month = true`, which hides marks after calculation. It has **no ordinary date filter**.
8. The bars filter `Is Month Selected? = true` before aggregation, then use `SUM(Sales)/MIN(No. Months)`, with `No. Months = DATEDIFF('month',min,max)+1`.
9. Selecting Bars applies an ordinary Sub-Category action filter to Trend. Monthly totals and the rolling average are recalculated for that category selection. Bars retain their full category comparison.

This gives the required behavior at a zoom boundary. For June 2018, sales are 34,595.1276, while the trailing average includes April and May and is 28,846.2532. An early date filter would incorrectly return 34,595.1276 for that first selected month. January's average has one observation (14,236.895); February's has two (9,378.3935).

## Addressing, partitioning and interactions

The trend has continuous `EXACTDATE(Order Date Month)` columns, Sales and Rolling Average rows, a synchronized area/line pair, and no additional detail dimensions. Both table calculations explicitly address `Order Date Month` using Field ordering. No level break, restart, or sub-category partition is configured. Natural ascending exact dates retain all 48 months, including distinct Januaries in different years. Bare date expressions would be defaulted by chart construction to a date part, so the explicit EXACTDATE selector is essential.

The SDK serializes the address as the raw date-calculation field, which is equivalent to the exact-date dimension instance used on the shelf. Verification accepts only those two exact field references, never a month-of-year date part or an unrelated field. Date action source fields must match the actual continuous exact-date shelf instance.

Dragging dates sets the minimum and maximum selected dates; noncontiguous selected months intentionally select the entire min/max envelope. Clearing trend selection resets both parameters to 1900-01-01 and therefore restores global data bounds. Sub-category actions support multiple selected marks and clear back to all categories.

Several categories have missing observed months: Copiers has 32, Machines 39, Supplies 44, Bookcases and Envelopes 46, Fasteners 47. Neither the author nor this builder explicitly requests date-domain padding. The SQL oracle uses the previous two **observed** monthly marks, matching the declared window. Tableau's native handling of missing dates must still be confirmed by the parent using Copiers and Machines; SQL evidence is not a runtime assertion about densification. The calendar denominator for bar averages remains the entire selected calendar interval, not the count of nonempty months.

## Scope and visual differences

The dashboard is 800 × 1000, as required by the official challenge. It has one trend and one two-panel bar worksheet. Colors, padding, labels and typography are independently chosen. The author's development crosstab is omitted. Date actions are scoped explicitly to Trend rather than all dashboard sheets; this avoids dispatching absent date fields from bar selections. The original challenge's web-authoring-only exercise is intentionally outside this SDK replication workflow. Saved Cloud rendering supports `acceptable_delta`: category names are readable and values available. Color, axis ticks, numeric bar labels, panel proportions and typography differ; no pixel-match claim is made.

## Released SDK result

Baseline: cwtwb **0.29.0a1**, commit **23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c**, source `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`. Each command explicitly sets both `PYTHONPATH` and `CWTWB_SRC`. The builder rejects other SDK versions. No a2 switch, global installation change, SDK edit, author XML workaround, or reusable missing capability was needed. Local construction result is `pass`; overall functionality stays `partial` until the mandatory runtime gates pass.

The verifier checks all calculation formulas, continuous month grain, both table-calculation addressings, absence of partition resets/extra dimensions, late versus early date filters, synchronized axis binding, both bar shelves, sort direction, date parameter defaults, parameter action min/max/reset semantics, sub-category action scope, data packaging, and XSD. It compares 27 scenario outputs between the independent Decimal oracle and Hyper SQL model, including zoom, single month, first two months, year boundary, final month, all 17 sub-categories, multiple categories, and reset. Six deliberate contract mutations must fail verification.

## Local evidence and parent-owned gates

`evidence/local-verification.json` contains every numerical scenario, contract details and the tested artifact hash. `evidence/handoff.json` binds the final frozen workbook, exact commands, SDK source/commit, local gate results and remaining work. `evidence/runtime-pending.md` gives the runtime acceptance procedure.

An isolated copy is rebuilt with `run_case_scripts_isolated`; metadata/catalogue checks run without changing the frozen artifact. The current catalogues are regenerated after parent authorization. All 83 repository tests pass. Parent evidence records the same frozen artifact as LOADED and the 50-case corpus as LOADED=50, FAIL=0, UNKNOWN=0.

Saved REST exports cover default, June 2018, Copiers and Machines: 48, 1, 32 and
39 observed monthly marks. `verify_runtime_exports.py` checks manifests and every
trend/bar value against the raw-row oracle and author Data sheet. June retains
rolling 28,846.25 rather than sales 34,595.13. Machines' first three observed
months (March, April, June 2018) yield rolling 25,314.66, 12,801.31 and 8,764.80.
This is bounded observed-mark coverage, not exhaustive dashboard densification.
REST category filters directly affect Bars and do not exercise the native action.
Actual drag/min-max aggregation/clear/repeated zoom/multi-select/reset and action
isolation remain pending because browser MFA is unavailable. Functional status
remains partial; independent review and its limitations are preserved separately.
