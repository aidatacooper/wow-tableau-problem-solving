# WW41: top sub-category contribution to sales

## Identity and business question

- Article: https://donnacoles.home.blog/2021/10/14/how-much-do-top-sub-categories-contribute-to-sales/ (2021-10-14).
- Official challenge: https://www.workout-wednesday.com/2021w41tab/ (2021-10-13; WordPress record 6077).
- Author: https://public.tableau.com/views/2021_10_13_WW41_PieChart/2021_10_13_WW41_Pie_Chart.
- Canonical ID: `wow-2021-ww41-how-much-do-top-sub-categories-contribute-to-sales`.

A sales team needs to see how much revenue is concentrated in its highest-selling
sub-categories. A user chooses N from 1 to 17. The inner pie compares their combined
sales with the remainder; the outer ring provides sub-category detail. A grouped
highlight table provides precise sales and ranks. Hovering a mark highlights the
same Top N/rest group in both views without filtering away the sales denominator.
The official dashboard is 1400 x 900.

## Analysis boundary and raw data

Inspected the local article and targeted author TWB nodes during analysis only.
The source archive contains one TWB and one Hyper. `prepare_case` extracted the
Hyper exactly once; the source and extracted hashes are in `inputs/source-lock.json`.
No author XML or workbook is copied into this case, builder, or synthetic repro.
The builder reads only that extracted Hyper and uses public cwtwb authoring APIs
starting with `TWBEditor("")` and `set_hyper_connection`.

`Extract.Extract` has 9,994 rows and two fields: `Sub-Category` (text) and `Sales`
(double). There are 17 distinct, non-null categories, no tied category totals,
and total sales of 2,297,200.8603. This is the packaged snapshot, not a newly
downloaded Superstore edition. No preprocessing alters or aggregates the input.
The builder calculates only a color/order mapping from the input; all marks
still aggregate raw sales through Tableau.

## Tableau solution chain

Raw sales -> integer parameter pTopN -> descending SUM(Sales) Top N set ->
Group Order / Sales Group -> two synchronized Pie panes + grouped Bar table ->
dashboard parameter control + on-hover highlight action -> group contribution.

- `pTopN`: default 5, integer range 1..17, step 1.
- `Top Sub-Categories`: native parameter-driven set ranked by SUM(Sales).
- `Group Order`: 0 for top, 1 for rest; puts top group first in inner pie/table.
- `Sales Group`: dynamic `IN TOP n` or `ALL ELSE`; shared hover key on both panes
  and table. Matching on group intentionally highlights several sub-categories.
- `Total Sales`: `{FIXED : SUM([Sales])}`.
- `Top Share`: top-group `SUM(Sales) / MIN(Total Sales)`; null for the rest.
- `Pie Label`: rounded whole percent and dynamic TOP n text; blank for rest.
- Outer angle and inner angle both use SUM(Sales). Their dummy MIN(0) axes are
  synchronized; revised outer size 6.8, inner size 5.6. Inner pane is second/front.
  Native pie labels are hidden because Tableau places them outside the slice.
  Contribution Summary is a separate unfiltered text view above the pie: its
  dynamic TOP N / whole percent comes from SUM(IF set THEN Sales ELSE 0 END)
  divided by the FIXED total. It does not cover any pie marks.
- Outer categorical colors use input-derived `01 Phones`, `02 Chairs`, etc.
  Tooltip uses the real category. This gives sales order using lexical ordering
  without XML edits; see the a1 sort workaround below.
- Table uses equal-length MIN(1) bars, consistent category colors, descending
  sales, global RANK(SUM(Sales)), and sum subtotals by Sales Group. Group Order
  is hidden. Rank addresses all three row dimensions so it does not restart
  within each group. Native subtotal header supplies SUBTOTAL FOR GROUP.
  Rank Prefix displays a rank only when SIZE() equals the FIXED category count:
  17 detail marks versus 1/2 subtotal marks. This avoids misleading ranks recomputed
  across group totals and handles singleton groups at N=1/16. Its native runtime
  behavior is still subject to the parent Cloud check. Both the SIZE() context and
  the nested Sales Rank context explicitly address Group Order, Sales Group, and
  Sub-Category; leaving the nested rank at Rows produced #1 on every detail mark
  during the first Cloud correction round and is specifically rejected now.
- One dashboard-wide hover action brushes Sales Group, auto-clearing on leave.
  It is a highlight, not a filter, so the total and pie proportions stay fixed.

## Important difference from the article

The author's inner angle sums a FIXED group sales calculation repeated on each
transaction. That weights a group's angle by its row count. We deliberately use
SUM(Sales) for both inner and outer angles to meet the official sales-proportion
requirement. The percentage is computed independently from the same raw total.
Author XML is neither copied nor treated as an expected numerical oracle.

## Observable numerical acceptance

All 17 parameter states are recorded in `evidence/numerical-oracle.json`.
At N=5 the members are Phones, Chairs, Storage, Tables, Binders: 1,292,678.03
(56.2718764536%, displayed 56%); remainder 1,004,522.8303.
At N=1 only Phones is top: 330,007.054 (14.3656159852%, displayed 14%).
At N=16 the remainder is Fasteners: 3,024.28; top is 99.8683493441%, displayed
100% by intentional whole-percent rounding, while a nonzero rest slice remains.
At N=17 top is 2,297,200.8603, rest is zero and there is only one populated group.
Outer 17 category sales, ranks, proportions and colors stay constant for all N.
Group subtotals sum to the fixed total; membership changes monotonically as N rises.

## Released SDK baseline and workarounds

Only cwtwb **0.29.0a1**, commit **23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c**, was
used. Source: `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`.
Each process explicitly sets PYTHONPATH and CWTWB_SRC. The global editable
install and shared SDK are untouched. a2 was not tested.

Two author-free reproductions are in `evidence/sdk-gap-repro.py`:

1. `configure_custom_label` recursively looks for a datasource column for a set
   and raises `ValueError: No datasource column for [Top Set]`. Native sets are
   represented by groups, not columns. Workaround: compose the two-line label in
   a string calculation and use dual-axis `label_2`; use pane datalabel styling.
   Proposed fix: shared set-aware dependency handling that accepts the registered
   group and emits its InOut instance, without inventing a column. Preserve the
   custom-label builder -> chart facade -> TWBEditor -> MCP -> capability path.
   Add a synthetic XPath regression for a rich label that indirectly references
   a parameter-driven set, including atomic invalid-request handling.
2. `configure_dual_axis(sort_field='Category', sort_descending='SUM(Value)')`
   rejects Category when it is only on Color: `sort_field must identify a
   dimension on the row shelf`. Workaround: a lexical key generated from raw
   category totals. Proposed fix: support computed sorts for encoding dimensions,
   reusing the layered builder's existing `sort_mode=auto/computed/shelf` design
   through dispatcher, Python facade, MCP, capability registry. Add XPath tests
   for computed sort on either pie pane and preserve row-shelf sort regressions.
   Source inspection found that layered charts do not pass a wedge-size encoding
   to their pane setup in a1; they are not used as a pie replacement here.

Result is **workaround**. Both failures were reproduced on a1 before workarounds;
no SDK mutation or silent version switch occurred. This case's fixed data are
supported. If the underlying snapshot changes, rebuild so the lexical key tracks
its new sales order; live-refresh ordering is not claimed.

## Verification scope and remaining gates

`verify_replication.py` never imports the builder. It accumulates individual raw
rows with Python Decimal, independently aggregates the generated package's Hyper
with SQL, and checks generated parameter/set/calculation/encoding/rank/subtotal/
action contracts before comparing all 17 states. It verifies package input hashes,
color consistency, and XSD; eight deliberate semantic mutations must be rejected.
This is a checked semantic model, not execution by Tableau/VizQL.

The current frozen workbook SHA256 is
`7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb`.
Parent-provided `evidence/desktop-parent-check.json` confirms **LOADED** for these
bytes; `evidence/desktop-corpus.json` records the existing 50-case regression
corpus as **LOADED=50 FAIL=0 UNKNOWN=0**. Cloud REST renders and 20 worksheet CSVs
cover N=1,5,16,17 and are bound by `cloud-verification.json` and `cloud-csv.json`.
Independent review rechecked the raw Hyper, all 17 category values and global
ranks at the four states, group subtotals, blank subtotal ranks, dynamic summary
and two-view action scope. It found no confirmed defect in that reviewed scope.
See `evidence/independent-final-review.json` and its byte-preserved report.

The earlier clipped pie text and subtotal rank issues are corrected in these
captures. The contribution summary is readable in all four states; detail ranks
remain 1..17, including singleton groups at N=1/16, and subtotals have no rank
prefix. N=16 intentionally displays rounded 100% while the Fasteners remainder
stays nonzero. The inner pie uses sales-proportional angles instead of the
author's row-count-weighted angle, so exact screenshot equality is not expected.

Visual status is **acceptable_delta**. Accepted differences include the separate
summary heading, custom hue palette, typography and native subtotal placement.
Functional status remains **partial**, verification **pending**: REST parameter
requests and static action XML do not demonstrate interactive browser events.
Browser MFA prevented real pTopN control operations and two-way hover/auto-clear
checks. Complete `evidence/runtime-pending.md` before promoting those statuses.

Frozen outputs are never rebuilt in place during delivery validation. Use the
repository's disposable-copy validation entry point; original baseline probe
and reports remain explicitly historical. `README.md` gives reproducible
commands and links the final delivery checks.
