# WW2021 W42 — Reference date range through native set actions

## Identity and sources

- Article: https://donnacoles.home.blog/2021/10/21/can-you-use-set-actions-to-create-a-reference-date-range/
- Official challenge: https://www.workout-wednesday.com/2021w42tab/
- Article date: 2021-10-21; official publication: 2021-10-19; year/week: 2021/42.
- Canonical ID: `wow-2021-ww42-can-you-use-set-actions-to-create-a-reference-date-range`.
- Author workbook: https://public.tableau.com/views/2021_10_20_WW_42_Date_Range_Set_Actions/2021_10_20_WW42_Date_Range_Set_Actions
- `case_intake.py` ran read-only in the original archive checkout. It confirmed
  the official WordPress record 6095, title and date. Source archive SHA256 and
  extracted input hash are in `inputs/source-lock.json`.

## Business question and required result

How does sales performance in user-selected months compare with the complete
sales history, and which states account for that selected period's sales?
Keep the full history visible so the user can choose another period without
first clearing a filter. Show total and monthly average, first-to-last change,
the strongest selected month, top-state contributions and a geographic view.

The official challenge explicitly requires native SET ACTIONS and disallows
filter actions. A parameter-only imitation, a static initial range, or a range
filter that removes the rest of the trend would not satisfy the core behavior.
The reference band's endpoints summarize the selection; membership determines
the selected measures. These are different for noncontiguous selections.

## Analysis-only author findings

Inspected the archived TWBX through ZIP member enumeration and selected XML
nodes only. No complete TWB was dumped or copied to this case. The archive
contains one 262,144-byte Hyper extract and one TWB. The extract has exactly
`Order Date` (date), `State` (text) and `Sales` (double), 9,994 raw rows, 48
distinct months and 49 states. It is not a pre-aggregated replication result.

The author has six displayed sheets plus analysis sheets. The displayed views
are overall summary, selected-period summary, dual-axis monthly trend, state
donut, top-three state table and US map. The date set initially contains the
nine months October 2020 through June 2021. The native action runs on select,
assigns marks to that date set and uses `do-nothing` on selection clear.
The band endpoints are global selected minimum and maximum months. State
views filter by membership before ranking; rank <= 3 is a table-calculation
filter so percent-of-total still uses all selected states. The trend combines
all-sales and selected-sales lines, synchronized, with a selected-peak label.

The source uses nested monthly FIXED LOD expressions for averages. This build
states the arithmetic business definition directly: total divided by distinct
months. It does not assert equivalence to the author's rendered averages until
the parent's runtime comparison. Monetary values remain unrounded in the data;
formatting is applied only to display.

## Independent construction

`prepare_case.py` extracted the data once, before authoring. The builder reads
that Hyper and starts with `TWBEditor("")`. It never imports an author workbook,
reads author XML, patches generated XML, reads verifier output, or loads a
prebuilt workbook. Only public cwtwb calls author the datasource, calculations,
set, six sheets, 1000×800 dashboard and action. No parameters exist.

Calculations are derived from these definitions:

- Month = first calendar day of the order's month; set membership is native.
- Overall total is global SUM(Sales); global average is total / distinct months.
- Selected Sales is Sales for set members and null otherwise. Selected total
  sums it; count counts distinct selected months; average divides these values.
- First/Last Month are global selected extrema. Their sales are global sums
  for those exact months. Change = (last sales − first sales) / first sales;
  zero denominators and empty sets return null.
- State views apply the selected-membership filter. Sales rank is descending
  competition rank; share is state sales / window sum across every state.
  The top-state table subsequently filters ranks 1–3. Donut color uses that
  rank, with one shared color for every lower rank.

On clear, the serialized action leaves membership untouched. On a new mark
selection, assignment replaces it. No default-on-clear reset is added.
Empty-set calculation tests are robustness tests, not a claim that clearing
marks empties the set. Single-month selection has a zero-width reference band
and zero endpoint change. Noncontiguous selection counts only chosen months,
although the band spans the minimum/maximum interval.

## Verification and evidence

`verify_replication.py` checks the package input hash, XSD and contracts for
sheet encodings, date members, native action and clear mode, band bindings,
set filters, ranking filter, text measures and native map. It reads emitted
formulas and uses `formula_oracle.py` to parse a restricted expression grammar
into Hyper SQL. Unknown syntax fails closed. Separately, Python groups raw
rows and uses `math.fsum` to form the independent numerical oracle. The builder
does not import either verifier module.

Six states are evaluated: default nine months, Q1 2019, June 2021 alone,
October 2020 plus June 2021 only, all 48 months, and an empty set. Every monthly
point, selected point, selected peak, state sum, rank, share and color group is
compared, in addition to the summary figures. Tolerance is absolute 1e-6 or
relative 1e-10 to accommodate floating-point aggregation. `test_verifier.py`
mutates calculations and interaction contracts to ensure real regressions are
rejected. Detailed expected values are in `evidence/local-verification.json`.

Global total is $2,297,200.8603 and average $47,858.35125625. Default selected
total is $493,007.986; average $54,778.66511111111; change −11.235169464%; peak
December 2020; top states California/New York/Washington. Disjoint October/June
total is $112,669.4707 and count is 2, demonstrating why the band is not a filter.

SQL evaluation verifies formula semantics, not Tableau VizQL or live UI
execution. No Desktop, Cloud, geocoding/render, interaction or corpus result
is claimed. `evidence/runtime-acceptance.md` provides the parent's exact event
sequence and expected state changes. Functional status remains **partial** and
visual status **not_evaluated** until those mandatory gates pass.

## Released SDK baseline and differences

Tested only cwtwb **0.29.0a1**, commit
`23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`, from
`C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`.
Every SDK process explicitly sets PYTHONPATH/CWTWB_SRC. The global editable
installation was not changed; a2 was not substituted; shared SDK code was not
edited. Native date members, set actions, exact-date band and chart construction
are supported by the a1 public APIs. Local baseline result: **pass**, scoped
to construction/XSD/formula/contracts, with runtime gates pending. No reusable
capability blocker has been reproduced, so no synthetic SDK issue/PR is proposed.

Allowed differences: layout, padding, font sizes, currency display precision,
title wording, map palette, and donut wedge order. Wedges retain the SDK's
default state order rather than author descending-sales order; the ranked
colors and angles still use selected-state sales. Arithmetic-average definition
is explicit, and any author/runtime discrepancy must be assessed by the parent.
No pixel-match claim is made. The XSD validator's missing trailing
`referenced-extensions`/`explain-data` compatibility warning is recorded, not
treated as a strict schema failure or proof of Desktop acceptance.

## Handoff boundary

The parent owns Desktop LOADED, native selection/clear event tests, rendered
comparison, independent review, corpus regression, shared generated indexes
and final PR. This case intentionally does not change the shared catalogue.
Run validate_iteration before freezing evidence, as it rebuilds UUID-bearing
artifacts. The final artifact hash and exact commands are in handoff.json.

## Coordinator retest after baseline

The released a1 local-only conclusion above is superseded by observed Cloud
behavior: Text chart addressing was dropped, giving every state rank 1 and a
100% share. A separate generic SDK candidate repairs forwarding through Python,
MCP and run-spec, and native-set dependencies in custom labels. The original
baseline evidence is archived without replacing its historical conclusions.

The candidate uses public layered charts so both date endpoints are bound on
the pane holding the reference band. Explicit Field addressing now labels only
the selected peak and ranks states correctly; a pane-local color mapping renders
the donut rank groups. Final Desktop is LOADED, the existing 50-workbook corpus
passes, and independent review found no confirmed defect in default Cloud data
and rendering. See evidence/candidate-runtime.md and independent-review.md.
Real native selection and clear events remain pending; functional status is partial.
