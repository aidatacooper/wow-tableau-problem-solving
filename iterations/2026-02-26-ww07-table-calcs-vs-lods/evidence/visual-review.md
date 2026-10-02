# Cloud visual review: WW07

Scope: real Tableau Cloud REST PNG/CSV exports plus native artifact contracts;
no browser selection, hover or dropdown interaction was executed.

The final baseline replica matches both native calculations' twelve labeled
bars, four alphabetically ordered Regions and descending Category sales within
each Region. Orange table-calculation bars and blue LOD bars sit in corresponding
pastel bordered panels, with the same section/filter/chart organization.
Consumer filtering recalculates the category proportions in both charts.

CSV: the eight actual dashboard exports select LODs only (twelve, twelve, two rows
for baseline, Consumer and the two Consumer/East category requests). All sales and rounded percentages match independent
Hyper arithmetic. They do not cover the Table Calcs worksheet.

The physical Category REST filter used for the third state affects both sheets'
underlying source, even though the TC quick-filter control stays All. Both author
and replica consequently render TC Technology56.2% / Office Supplies43.8%, while
LOD retains37.9% /29.5%. This is an export-request scope effect, also observed in
the original; it does not exercise the TC LOOKUP late filter. The artifact
contract and independent Hyper oracle prove that late-filter definition. The separate
consumer-east-tc-late-filter request omits physical Category and applies
TC - Filter Category instead. In both actual author and replica PNGs, the orange
Table Calcs chart correctly renders Technology 37.9% and Office Supplies 29.5%
with Furniture hidden. Those percentages match the Consumer/East baseline; their
sum is below 100%, establishing the intended late-filter denominator behavior.
The same request also hides Furniture in the LOD chart while preserving its
percentages. The additional pair of CSV exports still covers LODs only, so this
TC proof is explicitly visual plus the executable native artifact/data contracts.

Accepted presentation differences: centered rather than left title/instructions,
colored section text, TC filter caption exposes its calculation name, hidden
row field titles, slightly different padding/axis positions, and stretching
the two filtered rows to fill the pane instead of the author's fixed row height.
The official challenge says700high, while both author and replica740high.
These do not change the established analytical contracts. Pixel equality is
not claimed; intended visual status is acceptable_delta after coordinator review.
