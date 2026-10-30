# Analysis: 2021 Week 49 frequency matrix

## Identity and source analysis
Article publication: 2021-12-12. Official challenge: 2021 Week 49,
published 2021-12-08T08:00:59 (WordPress post 6494, API evidence saved).
The article's first Tableau link is the historical 2018 solution; it is NOT
this case. Correct author workbook is 2021_12_08_WW49_FrequencyMatrix.
Source lock retains the original archive hash and once-extracted Hyper bytes.
The author XML was inspected only during analysis, with bounded summaries.
Both packaged raw tables have the same 9,994 (order, sub-category, sales) rows.

## Business question and required behavior
Find distinct orders containing a pair of different sub-categories and compare
each category's average sales contribution within those orders. Rows are the 17
uppercase categories alphabetically; columns are NONE followed by the same
alphabetical categories. NONE means no second category exists for that order:
multiple lines of the same category still belong to NONE. It is neither an
all-orders total nor a diagonal replacement. Exclude diagonal and repeated
symmetric combinations. Show one triangular matrix of counts as square marks,
with the ColorBrewer BuPu ramp and labels. Upper cells are blank white.

The official constraint is one logical data source, one worksheet, 1100 x 900,
logical modeling, and no LOD expressions. The author relates Order ID = Order ID
AND Sub-Category <> Sub-Category, then uses distinct order count and nested
INDEX table calculations with field-specific addressing. Row index >= column
index retains NONE plus the strict lower triangle because NONE shifts columns
by one. Category labels are rotated -90 degrees on columns.

Tooltips have a row title, optional ` & SECOND CATEGORY`, distinct order count,
singular SUB-CATEGORY for NONE or plural SUB-CATEGORIES otherwise, and separate
SUM(category sales)/COUNTD(order) dollar values. The second category label and
colon are absent for NONE. The source dashboard has a hover instruction,
attribution and challenge URL. Bounded inspection found no dashboard actions,
parameter controls, user category filter, or color legend. None is added here.
Native mark selection may highlight, but must not filter/reindex the domain;
clear selection restores normal appearance. The only worksheet filter in this
rebuild is the table-calculation triangle filter. The source's extra null-row
exclusion is unnecessary because the input domain has no null category keys.

## Data construction and numerical semantics
A raw physical line self-join would multiply sales when both categories have
multiple lines in an order. The builder aggregates sales once per order/category,
then expands eligible distinct category pairs. Single-category orders expand to
NONE only. Every ordered category pair also receives a domain row; missing pairs
have one NULL order scaffold with NULL sales so COUNTD is zero and visible count
is NULL. Diagonals have no real facts and are removed by the triangle filter.

The emitted Hyper has Pairs (one row per cell) and Contributions (one row per
eligible order/cell), connected via a public logical relationship on Pair Key =
Fact Key. The complete domain preserves INDEX positions even with missing pairs.
Column Sort is numeric BIGINT: descending negative ordinal puts NONE first,
then alphabetical columns. Rows use default ascending string ordering.
The model retains all ordered pairs, so exchanging row and column preserves
counts but swaps their potentially very different sales contributions.
No probability/percentage denominator or category-selection parameter is part
of this challenge. Tooltip denominators are the distinct orders in each cell,
never all orders involving the row category. Preprocessing is deliberately a
case workaround, not a claim that the SDK cannot express other equivalent models.

## Public SDK baseline and boundary
Baseline is the published prerelease cwtwb 0.29.0a2, loaded explicitly through
PYTHONPATH and CWTWB_SRC. PyPI stable 0.28.0 was not the requested baseline.
Public APIs used: blank TWBEditor, set_hyper_connection with explicit typed
logical tables/keys, add_calculated_field, configure_layered_chart with explicit
shelves and nested field-addressed table-calculation overrides, worksheet style,
custom tooltip, add_dashboard and save. No private SDK objects or XML mutation
are used by construction. No SDK modification or reusable gap is claimed.
The builder reads only extracted Hyper data. Installed-distribution provenance
(version, imported module path/hash) is recorded without requiring a local Git
checkout. Custom currency uses Tableau's `*` format prefix. The BuPu colors are
embedded explicitly, so the user's custom palette installation is unnecessary.

## Independent verification and limits
The verifier queries raw lines using indexed SQL EXISTS/NOT EXISTS separately
for each category, grouping sales only after order eligibility. It does not
reuse the builder's Python expansion. It compares every actual packaged fact's
order eligibility and both sales amounts, all 306 domain cells, and emitted
COUNTD/SUM formulas and bindings. A small independent fixture covers duplicate
lines on both sides, a three-category order, duplicate single-category lines,
asymmetric sales and a missing pair. Mutations corrupt formulas, dependencies,
addressing, sort order, tooltip, key, format, mark, worksheet count, facts and
NONE membership; all must be rejected. Formula/dependency closure includes
physical metadata, worksheet instances, shelves, styles and tooltip references.

Static checks cannot prove Tableau's runtime table-calculation behavior, dollar
rendering, square sizing, tooltip hover, or white upper-triangle appearance.
Functional status stays partial, visual not_evaluated, verification pending
until the parent runs Desktop and render/hover checks. No live-event evidence is
claimed. Font/padding differences are acceptable if labels and values remain
readable. Runtime check instructions are in HANDOFF.md.

Explicit table_calc metadata is supplied for both INDEX fields and the nominal
boolean measure Triangle so its instance uses User derivation. The earlier
None-derivation workbook is retained only as outputs/role-probe.twbx, declared
role probe with a supersession note. It has no runtime pass claim.


## Completed real browser acceptance (supersedes pending interaction notes)

Real NONE and two category-pair tooltips passed all counts, currency and conditional text. Native selection/clear preserved the 153-cell lower triangle and category order. Artifact SHA256 remains `09708672f5f140fb57f4d07d335c65610d8a5ff9a201378050a11ba508849dde`. Evidence: `evidence/browser-20261030/report.json`. Functional replicated, verification verified, visual acceptable_delta, SDK workaround. No SDK/builder/artifact edits or new Desktop/corpus run; existing hash-bound gates still apply.
