# WW2019 Week 48 ? Automatically combine small contributions

Donna solution article: 2019-12-02, https://donnacoles.home.blog/2019/12/02/can-you-build-a-bar-chart-that-automatically-combines-small-contributions/
Official challenge: 2019-11-27, https://www.workout-wednesday.com/week-48-can-you-build-a-bar-chart-that-automatically-combines-small-contributions/
Official WordPress record 3048 reports `2019-11-27T14:44:29`; this is the publication calendar date, not inferred from the workbook name.

## Business question and source analysis

Show every state's contribution to total Superstore sales. The user chooses a minimum sales share; states below that threshold collapse into All Other States. Retained states sort largest first, but the combined group always appears last, even when its summed sales exceed individual states. The title reports how many states remain listed and how many are grouped.

The original analysis-only TWBX is downloaded under ignored `dashboards/2019_11_27_WW48_Sales_by_State/2019_11_27_WW48_Sales_by_State.twbx`. Source-lock records its SHA-256 and the single extracted Hyper file. The builder never reads this archive. The original dashboard is `2019_11_27_WW48_Sales_by_State`, 1100 x 900. Worksheet Viz uses dual horizontal Bar and GanttBar axes; invisible Gantt bars at zero position labels above the visible bars. Teal retained states and grey Other marks, table-wide threshold line, percent type-in parameter default .03, and dynamic count title complete the chart. There are no action contracts.

The author uses a FIXED total plus a row-repeated LOD percentage. The replica calculates `State Contribution={FIXED [State]:SUM([Sales])}/[Total Sales]` for classification and `Sales/Total Sales` summed for displayed bars. These are mathematically equivalent, while avoiding surprising row-count weighting in the row-repeated source calculation. Complete Hyper SQL aggregation provides an independent oracle.

## Acceptance and scope

`verify_replication.py` asserts parameter defaults, inclusive threshold boundary, grouping formula, sort contract, two synchronized panes, dual labels, two dynamic counts, parameter-backed reference line, and dashboard control. Numeric evidence covers all 9,994 source records and 49 states, total sales 2,297,200.8603. At 1% there are 23 retained / 26 grouped states (24 displayed bars); at 3%, 10 / 39 (11 bars); at 5%, 5 / 44 (6 bars). All rows must sum to 100%; California remains largest and Other remains last. Independent expected rows live in `evidence/local-verification.json`.

Root coordinator will publish original and replica, export high-resolution images for default 3% and additional 1%/5% REST parameter states, and export Viz CSV covering every grouped bar. Suggested REST parameter caption `Threshold Percent`, values `0.01`, `0.03`, `0.05`. CSV validation must reconcile State Grouping and aggregated % Sales Per State for every bar; title counts are additionally asserted from independent data and artifacts. No browser clicks or hover events are claimed.

## SDK feedback and limits

The released SDK layered API provides independent labels, colors and tooltip fields but originally lacked descending sorting. This case motivated a generic `sort_descending` option across layered builder/dispatcher/facade/MCP, coordinated in the SDK repository with a synthetic regression. Parameter-backed threshold reference line uses an ordinary row calculation and the existing public `add_reference_line`; no special API was needed. The source itself acknowledges labels can overlap under some threshold values. Final Cloud render review must record any observed spacing/font/title/tooltip differences and must not claim pixel parity.

Local status remains partial/not_evaluated until complete Cloud comparison, CSV validation and artifact hash binding. Rebuilding after capture invalidates hashes and requires republishing.

## Cloud baseline feedback and corrections

Initial REST images revealed a table calculation partition error: simple Rows addressing produced per-mark counts (0 to 1) rather than 10 listed states. Counts now explicitly address both State Order and State Grouping with structured Field ordering. Initial Cloud colors also exposed a generic SDK numeric-palette bug: integer buckets were quoted as strings, causing Tableau to ignore colors. SDK typed palette serialization now writes numeric buckets unquoted. Artifact verifier checks both addressing fields and numeric bucket literals. Hidden row label formats, table divider removal, visible percent axis and a prefix separator for labels restore the original core composition.

The initial six author/replica CSV exports cover every grouped bar and reconcile all expected percentages at 1%, 3%, 5% within 0.005 percentage points (two decimal percentage rounding). This proves complete bar data but did not prove the incorrect initial title. Recapture is required after corrections; final CSV count columns must equal the independent expected counts on every bar.
