# WW07: regional sales percentages, two independent calculation routes

Article: Donna Coles, 26 February 2026, Exploring Table Calcs vs LODs.
Official challenge: 2026 Week 7; publication date 17 February 2026 was read from
WordPress REST post metadata, rather than inferred from the workbook filename.

## Business behavior

Compare category sales within each region. Region removal must leave every other
region unchanged. Segment selection must recalculate both numerator and regional
denominator. Category removal hides its bar but preserves the denominator and
remaining percentages, so visible percentages may total less than 100%.

## Independent construction

The author's packaged Hyper has 10,194 input rows and only Segment, Region,
Category and Sales. Its source-lock records the original package and extracted
bytes. The builder starts empty and uses two native charts. The table-calculation
route uses TOTAL(SUM(Sales)) explicitly addressed by Category and a LOOKUP late
category filter. The LOD route uses FIXED Region/Segment before the category
filter. Both remain native Tableau calculations rather than precomputed numbers.

## Acceptance

The verifier checks packaged-data hashes, native filter types and addressing,
exact LOD denominator, six visible controls and an SDK round trip. Independently
aggregated Hyper rows establish all-segment, Consumer-only and Consumer/East with
Furniture hidden states. The last state preserves the Consumer baseline ratios.
The resulting numeric oracle is evidence/functional-verification.json.

Cloud author/replica PNG and full chart CSV states still require root-coordinated
publication. Worksheet names are Table Calcs and LODs. Filter request names are
Region, Segment, Category (LODs) and TC - Filter Category (Table Calcs). Author
and replica dashboard name is 2026_02_17_WW07_TableCalcs_and_LODs (1100 x 740).
The official challenge says 1100 x 700; the recreation follows Donna's 740-high
layout. Styling and footer placement may differ and must be reviewed against
real server renders. No browser clicks or hover execution are claimed.

## Cloud data scope and presentation refinement

The dashboard REST CSV selects only the LODs sheet: baseline and Consumer states
contain twelve rows each, Consumer/East with Furniture hidden contains two rows.
All six author/replica exports match the independent Hyper oracle. These CSVs do
not claim Table Calcs numeric rendering proof. Table Calcs remains independently
verified by its native TOTAL calculation, late LOOKUP filter and explicit Category
addressing; filtered Cloud PNG review must additionally inspect its displayed bars.

The refined dashboard adopts author positions for instructions, two orange/blue
bordered pastel panels, top filters and footer. The corrected generic SDK sort
addresses Category descending by Sales within each naturally ordered Region.
Native mark colors and eight-point row labels follow the author's chart.

A fourth real Cloud REST state, consumer-east-tc-late-filter, applies the native
TC LOOKUP filter without physical Category. Author and replica PNGs both render
Technology37.9% / OfficeSupplies29.5% with Furniture hidden, correctly preserving
the Consumer/East denominator. The fourth CSV pair remains LOD-only (two rows);
TC denominator proof combines those observed PNG labels and native artifact/data
contracts rather than misrepresenting CSV coverage.
