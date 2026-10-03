# Analysis

Article date: 2020-02-16; official 2020 WW07 was published 2020-02-11
(WordPress post 3470). The 1000 x 500 dashboard displays 2019 actual sales,
forecast bars and target Gantt marks for three categories. The author Hyper
extract already contains only 3,312 rows from 2019; the builder also explicitly
filters YEAR(Order Date)=2019. Original files remain analysis-only scratch.

Forecast List and Target List are delimited string parameters storing
Category_value: pairs. Forecast Param permits positive and negative increases;
Target Param only accepts positive updates. The Forecast starts null for an
unselected category, rather than zero. Defaults for unselected targets are
Furniture270000, Office Supplies260000 and Technology250000. Actual sales are
SUM(Sales); forecast adds the category's stored increase; both percentage
differences use (value-target)/target. REGEXP_EXTRACT retrieves the stored
category-specific number. Both selectors and both empty-string reset fields
have select parameter actions; True-to-False self-filters clear selections.

The replica replaces an existing category token with REGEXP_REPLACE before
appending a new value. The author append-only string can retain an earlier
value because its REGEXP_EXTRACT chooses the first matching token. Replacement
implements the official update requirement when a category is selected again.
Comparison REST states use unique category tokens so their metric values
remain comparable. The independent list-state checks cover adding two
categories, replacing Technology70000 by Technology10000, signed forecasts,
rejecting a negative target, and resetting empty. These are calculation and
artifact checks; no actual click is claimed.

The baseline SDK12aae31 has two generic gaps: it always writes pane breakdown
auto despite requested off, stacking Forecast and Sales; and Measure Names
color-map raises an unresolved-field error. A data-free A/B overlay fixture
records the first failure and the actual case-builder exception records the
second. The SDK now accepts per-pane breakdown and a virtual Measure Names
palette. The case uses a two-pane folded chart: Multiple Values contains
Forecast and Sales, with stack marks off, while Target is a black Gantt mark.
Both blue and teal bars retain their correct measure palette.

Six REST states cover default, positive forecast, negative forecast, updated
targets, combined changes and reset. Full Viz CSV must verify all three
categories' actual/target/forecast values and both differences. Selector or
reset CSV alone does not prove chart correctness. Cloud visual/data review passed for all six states with the tested SDK commit recorded in case metadata. The final scope and remaining differences are recorded in `evidence/visual-review.md`. No browser clicks or hovers are claimed.

Cloud review found that labels applied to both Measure Values bars overlap,
plain custom percentage strings render decimal ratios without Tableau's
custom-format prefix, and full-height chart rows do not align with the shorter
selector views. The final layout uses a 190-pixel chart and label band with native vertical-flow side panels, keeping each selector associated with its category row. It uses one separate Text label worksheet (six sheets total;
the challenge allows any number). Chart CSV still binds all five numeric
metrics as detail fields. Rounded signed percentage strings are calculated
for the label only; numeric differences retain native p0% formatting.

Measure Names must also bind the size encoding to make forecast bars thinner
than actual bars, so both remain visible. SDK2768dc0 omits this virtual size
binding; a synthetic CSV fixture records that third generic gap. The shared
SDK fix forwards the virtual field rather than inventing a physical column.

## Layout polish

Layout polish restores420px-high independent gray side-panel containers, enlarges selector and reset marks, corrects hollow/filled target-circle colors, thickens actual/forecast bars and target ticks, removes banding and reinstates title/subtitle/designer/footer hierarchy. Six parameter states and all measure/action contracts are unchanged; labels stay in an independent aligned column for readability.

The previously accepted workbook and complete evidence snapshot are retained in ignored scratch/polish-baseline-ww07. The polished artifact has been recaptured and accepted with documented visual differences; `evidence/visual-review.md` binds the final workbook hash and full evidence scope.
