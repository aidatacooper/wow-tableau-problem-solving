# 2021-07-29-ww30-let-s-go-streaking

## Problem

Sean Miller's Week 30 challenge asks a retention-style question about momentum:
for every product Sub-Category, **how many consecutive months in a row did
monthly sales rise, and what was the sales value in the month that closed the
longest such run?**

The dashboard must let a reader see, at a glance, which Sub-Categories built the
longest unbroken upswing and where in time that run peaked. That is a
_table-calculation_ problem, not an aggregation problem: "consecutive" is a
property of the ordered month sequence inside each Sub-Category, and no single
`SUM`/`MIN`/`MAX` expression can express it.

## Why the obvious approach fails

- `SUM([Sales])` per month answers "how much", never "how many months in a row".
- `{FIXED [Sub-Category]: MAX([Sales])}` finds the biggest month, not the end of
  the longest run; the two are unrelated.
- A month-over-month difference alone (`SUM(Sales) - LOOKUP(SUM(Sales), -1)`)
  only says "up" or "down". Turning that into a _count_ requires a value that
  carries state forward from the previous row — a recursive accumulator.
- Sorting the chart by `SUM(Sales)` or by the raw month order would put the
  wrong Sub-Categories on top. The list has to be ordered by the streak length
  itself, and the sort key must be a hidden discrete pill so the visible chart
  keeps the author's layout.

The article's chain is the minimum correct solution: it bakes a table
calculation into the data model (`Sales Diff`), derives a boolean "up" flag, then
compares each row's flag with the previous row's flag to detect the _start_ of a
run, and finally accumulates with `PREVIOUS_VALUE`.

## Tableau solution chain

```text
data (Order Date, Sub-Category, Sales) — 9,994 order lines, Jan 2016–Dec 2019
→ Order Date Month = DATE(DATETRUNC('month',[Order Date]))     (48 month buckets)
→ Sales Diff        = ZN(SUM([Sales])) - LOOKUP(ZN(SUM([Sales])), -1)
→ Diff Is +ve       = IF [Sales Diff] > 0 THEN 1 ELSE 0 END
→ Match Prev Value  = LOOKUP([Diff Is +ve], -1) = [Diff Is +ve]
→ Increase Streak   = IF (NOT match) AND up THEN 1
                      ELSEIF up THEN up + PREVIOUS_VALUE(up) END
→ Longest Streak    = WINDOW_MAX([Increase Streak])
→ Sales of Month with Longest Streak
                    = IF [Longest Streak] = [Increase Streak] THEN SUM([Sales]) END
→ Sort              = [Longest Streak] * -1        (discrete, hidden, leading row)
→ Chart: months on Columns (continuous exact date); Sort / Sub-Category /
  Longest Streak (discrete) / SUM(Sales) / Sales of Month with Longest Streak on
  Rows; stepped grey line pane + colour-ramped circle pane folded and
  synchronised on one row axis
→ Legend sheet: CASE-ordered Sub-Category squares on the same 5-step green ramp
→ dashboard: title strip, Chart, Legend, challenge/recreation credit strips
```

Every one of the seven table calculations is addressed **by `Order Date Month`
only**. That single choice is what makes `LOOKUP(...,-1)` restart at each
Sub-Category row instead of walking across the whole table.

## Required behavior

- `Order Date Month` buckets every order to the first of its month; the axis is
  a continuous exact date with 48 distinct points, not a month number.
- The streak chain exists exactly as above and each link is a table calculation
  addressed by the month bucket.
- `Longest Streak` is `WINDOW_MAX` over the streak and is repeated on every row
  of its Sub-Category.
- The peak marker is only non-null on rows where the running streak equals the
  Sub-Category's longest streak, so a Sub-Category with two equally long runs
  gets two circles (Tables, Chairs, Copiers, Machines, Binders, Storage all do).
- The list is ordered by `-[Longest Streak]` descending, which reproduces the
  article's leading rows: Appliances 5, Bookcases 5, Phones 5, Art 4.
- The colour legend is a fixed 0–5, five-step green ramp; the legend sheet uses
  the article's explicit `CASE` ordering (Art, Chairs, Labels, Paper, Phones).

## Oracle

`verify_replication.py` recomputes the whole chain in Python from the locked
Hyper extract — no reuse of the builder's formulas — and asserts:

| Sub-Category | longest streak | peak month(s) |
| --- | --- | --- |
| Appliances | 5 | 2017-11 |
| Bookcases | 5 | 2019-06 |
| Phones | 5 | 2019-09 |
| Art | 4 | 2019-06 |
| Envelopes | 4 | 2019-11 |
| Supplies | 4 | 2019-01 |
| Tables | 4 | 2017-09, 2019-11 |
| Binders | 2 | 7 tied months |
| Storage | 2 | 7 tied months |

The four leading rows and their streak values match the article's own
screenshots (`image-58.png`, `image-72.png`).

## Allowed visual differences

- Fonts, padding, borders and decoration may differ unless they affect the
  result.
- The author's Tableau-Regular/Medium display fonts are not shipped, so the
  title and credit strips use the workbook default family.
- The author's tooltip renders the month at month granularity; the replica
  renders the exact date. Text-only difference.

## cwtwb baseline

Built end-to-end with the public SDK only (no raw XML, no author workbook):

- `add_calculated_field(..., table_calc={"ordering_type": "Field",
  "ordering_field": "[Order Date Month]"})` writes the field-level
  table-calculation metadata.
- `configure_layered_chart(axis_shelf="rows", fold_axes=True,
  synchronized=True)` produces the author's three-part row shelf and the
  synchronised folded axis.
- `configure_layered_chart(sort_mode="computed", sort_field="Sub-Category",
  sort_descending="Sort")` emits `<computed-sort direction="DESC">` so the
  hidden `Sort` pill orders the rows without appearing in the view.
- `configure_worksheet_style(color_style={"colors": [...], "min": 0,
  "max": 5, "num_steps": 5})` writes `custom-interpolated` with a fixed domain —
  required, because a data-derived domain would normalise 2..5 across the ramp.

No workaround was needed and no reusable SDK capability was missing: the streak
chain, the folded dual pane, the computed sort and the pinned stepped colour
ramp are all first-class in the pinned SDK.


## Final runtime verification

The final Cloud dashboard shows all 17 Sub-Categories ordered by descending
longest streak, grey stepped monthly sales, green circles on all tied streak
endpoints, and a 0-5 legend. Native independent axes preserve each row's scale.
The leading rows are Appliances, Bookcases, Phones (5) and Art (4), matching
the author. All 4,896 exported month/category/measure cells agree with the
original author, including null sales in 34 missing category-months.

Accepted deltas: all rows fit in one dashboard rather than an initial scroll
viewport, Sort's negative grouping header remains visible, lines/circles and
legend are smaller, alternating row shading and min/max labels are absent.
Custom tooltips retain category and sales, while the axis supplies month.
No browser interactions are required by this static chart.

Result: acceptable_delta. Calendar scaffolding introduces only null-sales rows
for missing months; the streak chain remains native PREVIOUS_VALUE/WINDOW_MAX.
