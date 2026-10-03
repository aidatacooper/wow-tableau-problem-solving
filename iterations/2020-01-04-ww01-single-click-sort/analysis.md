# Single-click sorting, 2020 WW01

The earliest unconsumed actual challenge in `index.json` is Donna Coles's
2020-01-04 article. The 2019-07-16 entry is an introductory blog post rather
than a challenge. All earlier challenge articles already have formal cases.
The official WW01 post was published on 2019-12-31 (WordPress post 3317),
although its challenge identity is 2020, week 1.

The business question is which subcategories lead by total sales, sales per
order, or profit ratio. A 50-pixel header chooses a descending sort measure
for a three-column table. The active heading is dark with a downward arrow;
the other headings remain visible. Negative-profit subcategories use ruby
red bars in both the sales and profit-ratio columns. A zero reference belongs
only to the profit-ratio pane. The dashboard has exactly two worksheets,
700 x 900 dimensions, 50-pixel horizontal margins, a 4-pixel ruby band,
gray table background, hidden sort controls, and disabled tooltips.

Analysis uses the author's revised dashboard `2020_01_01_WW01_One_Click_Sort v2`,
with `Header v2` and `Table v2`. The earlier dashboard in the same archive
has a known selection-fading limitation and is not the reference. The
original archive and article remain in an uncommitted analysis directory.
Only its extracted Hyper is read by the builder. Source hashes are locked
in `inputs/source-lock.json`.

The revised author's parameter caption is `Sort (copy)`. Its string values
include spaces: ` Sales `, ` Sales / Order `, ` Profit Ratio `. A native
select parameter action takes Tableau's special Measure Names field. A
second select filter action maps True to False on the header itself and
clears to show all, implementing the published deselection technique.
REST parameter states verify resulting images/data; source, target, event,
and clearing semantics are validated from the artifact. No browser click
or hover is claimed.

The article defines Sales / Order as SUM(Sales)/COUNTD(Order ID). The downloaded
workbook expresses this through a FIXED subcategory distinct-order count;
Tableau's actual exported values confirm that the LOD aggregation gives the
same results. We implement the direct official metric and verify both author
and replica against independent fact-level aggregates. Profit Ratio is
SUM(Profit)/SUM(Sales). Independent Hyper aggregation covers all 17
subcategories and all three sort states; dashboard/header CSV alone cannot
certify every table cell.
SDK baseline revision `f0e385b` provides layered marks but always folds its
axes. The two-sheet design requires three independent side-by-side panes,
so requesting `fold_axes=False` fails with an unexpected-keyword TypeError.
It also lacks an API to hide sort controls. The generic enhancements add
optional axis folding and optional worksheet sort-control visibility, with
synthetic SDK regression tests. Baseline parameter-action Measure Names
resolution also incorrectly invents a physical field; the reusable fix must
preserve the special `[:Measure Names]` reference.

Cloud layout diagnostics found that a 50-pixel header pane renders as a blank
clipped area even though its standalone worksheet exports the three headings.
Removing the stripe, adding fixed stripe sizing, and changing the fit mode did
not resolve it; a taller header did. The author's
68-pixel Header v2 object height also failed in the generated composition.
The final layout uses the proven 100-pixel header, an explicit delta from the
official 50-pixel requirement and author's 68-pixel object. It retains exactly two worksheets and the 700 x 900
dashboard. This is a layout allowance, not a claim of pixel equality.

Visual acceptance permits documented differences in fonts, decorative
attribution, and pane spacing; selected headings, red signs, table ordering,
and the three independently encoded columns must remain legible.
