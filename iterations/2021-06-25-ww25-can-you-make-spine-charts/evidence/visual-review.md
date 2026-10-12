# WW25 Cloud acceptance — Can You Make Spine Charts?

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Sean Miller, resurrecting Emma Whyte's 2017 spine chart, rebuilt
by Donna Coles) shows one selected university's average agreement per question
against the overall average, with the min/max range and the inter-quartile band
drawn as reference bands.

## What was checked

- **Data**: the locked extract has 10,095 rows = 27 questions x 374 universities.
- **Selection**: `pUniversity` defaults to "The University of Liverpool";
  `University Avg` / `Sample Size` / `Overall Avg` / `Delta` / `Colour` match the
  article's formulas.
- **Values**: Q01 Liverpool 89.8% vs overall 89.1% (Delta +0.70%▲) and Q02
  82.4% vs 84.7% (Delta 2.30%▼) match the author's published screenshot; Q01
  min/max = 60%/100% and Q1/Q3 = 86.1%/92.5%.
- **Reference lines**: the black average line, the per-cell min→max band
  (`#f5f5f5`) and the per-pane quartile band (`#d9d9d9`).
- **Legend**: a fixed Middlesex University marker (74.76%) with labelled
  "Overall Min" / "Overall Avg" / "Overall Max" bands.
- **Layout**: 1366x900 dashboard with the legend strip under the title.

## Accepted visual differences

- Fonts and exact column widths differ; the article's screenshot uses a Times
  New Roman workbook font.
- The Legend sheet's band labels are placed by Tableau's automatic layout, so
  their exact horizontal positions differ.
- The row banding on the Viz sheet is approximated.

## Workarounds recorded

- `PERCENTILE(...)` is not in the released SDK's aggregation derivation map, so
  a field whose formula is a bare `PERCENTILE(...)` is registered as an unknown
  dimension and the pane renders empty. Passing `table_calc="Rows"` when adding
  the quartile fields makes them resolve as measures. A generic fix would add
  PERCENTILE to `_DERIVATION_MAP` / `_AGGREGATE_FUNCTION_RE`.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses
the article's written specification, the article's build screenshots and the
native workbook contracts.
