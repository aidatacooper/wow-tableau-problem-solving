# State profits and the top products inside each state

The 6 November article solves official 2020 WW45 (WordPress post 4060,
published 3 November). The author workbook supplies a 1000 × 800 profit map,
a nine-state eastern seaboard strip, and a 500 × 350 product worksheet embedded
in both tooltips. Original TWB/TWBX files are confined to analysis scratch;
the builder starts with `TWBEditor("")` and uses only extracted Hyper data and
public SDK calls.

The locked extract has 9,994 order lines, 49 states and five columns. Profit
and sales are summed from these lines. The map uses State geography, US lookup,
state abbreviations, no basemap layers, the original continental-US Mercator
extent, and a red–black continuous profit palette centred at zero. Small
seaboard states are represented in north-to-south order, each with a full-width
grey bar. A calculated measure provides north-to-south State sorting without reserving a second hidden row-header column.

The product table has a native Top 10 Product Name filter ordered by SUM(Sales),
State/Product rows and Orders/Sales/Profit columns, with a grand total. The
compound State Abbrev/State tooltip filter is in context: its filtering precedes
the Top N operation. Independent calculations cover every state/product pair,
global top products, and each state's top products; states with fewer than ten
distinct products retain all available products.

The article says Orders is COUNTD(Order ID), but the actual author worksheet
uses the `cnt:Order ID:qk` instance, including the Measure Names filter and
colour legend. Replication uses COUNT(Order ID) to match the published original.
The oracle additionally calculates distinct order counts and preserves the
distinction; it never substitutes them as proof of the source's Orders column.

Released SDK `eb1380d5da9c1b1bf1b306128cb8397150ba1a53` could not author
colour from the virtual Multiple Values field. A data-free synthetic public
request raised `Unknown field 'Multiple Values'`; the measure-values helper
also retained only a text encoding. This is recorded as a blocked baseline,
not a successful SDK run. The generic enhancement accepts the virtual colour
expression and independent measure domains in ordinary and layered charts.
Existing `color_style` configures the three native per-measure palettes.

REST validation requests the default state plus California, Texas and New York
ordinary State filters, exporting all three worksheets. The source tooltip
context is verified as an artifact contract. REST State filtering can differ
from an actual compound tooltip action; observed membership must be checked
against both global and state-local Top N before describing the export scope.
Neither dashboard images nor a button export prove an actual hover event.
Final Cloud acceptance is acceptable_delta at artifact 45fa3d27e106a459d7f4878e351f9a7847a80ffa904ca1d0d343aefd7664c749: all24CSV, eight dashboard images and eight standalone product images were independently reviewed. See evidence/visual-review.md for observed REST scope and remaining visual differences.

The first full Cloud capture exposed a second generic SDK dependency gap: the
compound target context group referred to State Abbrev, but the target worksheet
omitted that calculated member. Both the actual e598 artifact failure and an
exact released-SDK synthetic regression are preserved. The candidate recursively
registers each member's dependencies on both tooltip source and target; the
verifier requires real member columns and column-instances in the target.
Ordinary REST State exports cover only the global Top 10 products with facts
in that state, not state-local hover membership. Selected State filters replace
the seaboard member filter rather than intersecting with it.
