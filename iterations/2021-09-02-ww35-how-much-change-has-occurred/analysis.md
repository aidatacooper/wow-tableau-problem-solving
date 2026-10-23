# 2021-09-02-ww35-how-much-change-has-occurred

## Problem

Luke Stanke's Week 35 challenge asks a single question per Sub-Category:
*how much did Sales change between 2020 and 2021?* The answer has to be
readable in one glance without hovering, because the comparison itself is the
deliverable — a bar chart of two years side by side answers "which year was
bigger", not "by how much".

The author's published answer puts both years on the same row: a grey 2020 bar
with a coloured 2021 dot sitting on top of it, so the gap between the dot and
the bar end *is* the change, and the signed percentage is printed next to the
dot. Rows are ordered by 2021 Sales descending, and the 2021 value is shown as
a discrete pill beside the Sub-Category name.

## Why the obvious approach fails

- **Grouped bars.** Two bars per row halve the width and put the comparison on
  two different marks; the reader has to compare lengths across marks. It also
  does not show the magnitude of the change as a distance.
- **Difference-only bar (`2021 - 2020`).** Loses the base. +$26k on Phones
  (+33%) and +$26k on a small Sub-Category would look identical, and negative
  rows lose the scale reference entirely.
- **A table of three columns.** Accurate but does not answer the visual
  question the challenge asks; the point is the *shape* of the change across 17
  Sub-Categories.
- **Stacking the two years by default.** Tableau stacks bar marks by default,
  which makes the 2021 bar start where 2020 ends. The 2021 dot would then sit
  at `2020 + 2021` and every percentage would be wrong. Stack marks must be
  turned off, which is why the author's instructions call it out explicitly.

## Tableau solution chain

```text
data domain: Orders (Order Date, Sub-Category, Sales), 2018-2021
→ context filter YEAR(Order Date) in (2020, 2021)      [before the LoDs]
→ 2021 Sales = {FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2021 THEN [Sales] END)}
→ 2020 Sales = {FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2020 THEN [Sales] END)}
→ % Difference = (SUM([2021 Sales]) - SUM([2020 Sales])) / SUM([2020 Sales])
→ Rows: Sub-Category / discrete 2021 Sales pill
→ Columns: SUM(Sales) + SUM(Sales), synchronised, folded to one axis
→ pane 1 (Circle, on top): colour YEAR(Order Date (copy)), label % Difference
→ pane 2 (Bar, behind): colour YEAR(Order Date), 2021 drawn over 2020
→ sort: Sub-Category DESC by SUM(2021 Sales)
→ dashboard: sheet + challenge/footer credits at 700 x 800
```

The LoD is `FIXED [Sub-Category]`, deliberately *not* `FIXED [Sub-Category],
YEAR([Order Date])`: the author wants one 2020 value and one 2021 value per
Sub-Category, and the year filter is applied as a context filter so it does not
distort the fixed scope.

## Required behavior

- `ww35-year-window` — the view is limited to 2020 and 2021 by a **context**
  categorical filter on `YEAR(Order Date)`, and that filter is in `<slices>`.
  The extract holds 2018–2021, so the window is observable, not decorative.
- `ww35-subcategory-sales` — the extract reproduces the 2021 values printed in
  the author's pills and the 2020 values implied by the author's 2020 dots for
  all 15 visible Sub-Categories (and all 17 in the extract).
- `ww35-percent-change` — `% Difference` is the signed relative change and is
  rendered with the `+0%;-0%` format, so `Phones` reads `+33%` and `Machines`
  reads `-22%`.
- `ww35-descending-order` — rows are sorted by `SUM(2021 Sales)` descending:
  `Phones, Chairs, Binders, …` down to `Fasteners`.
- `ww35-dual-axis-panes` — two panes on one synchronised folded axis, `Circle`
  over `Bar`, both bound to `SUM(Sales)`; the bar pane is `x-index="1"`.
- `ww35-label-and-colour` — only the circle pane labels `% Difference`; the
  circle pane colours by `YEAR(Order Date (copy))` (2021 blue `#4e79a7`, 2020
  red `#e15759`) with a white stroke, and the bar pane colours by
  `YEAR(Order Date)` (2021 grey `#bab0ac` drawn on top, 2020 red `#e15759`).
- `ww35-dashboard-layout` — the sheet sits in a 700 x 800 fixed dashboard with
  the challenge author, week and URL credits.

## Allowed visual differences

- Fonts, exact bar width, paddings, borders and the scrollbar are not part of
  the contract.
- The replica prints `RECREATED WITH : cwtwb` where the author credits herself;
  the challenge/footer text is otherwise the same.
- The replica's label placement uses Tableau's range-scope label on the 2021
  dot rather than a hand-placed annotation.

## cwtwb baseline

Built entirely from the empty workbook with public SDK calls
(`set_hyper_connection`, `add_calculated_field`, `add_worksheet`,
`configure_layered_chart`, `configure_custom_tooltip`,
`configure_worksheet_style`, `set_worksheet_rich_title`, `add_dashboard`,
`save`) against cwtwb `0.29.0a1` (`23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`).

Two workarounds were needed and both are recorded in `case.yaml`:

1. **Discrete measure pill.** The author's blue pill is a *discrete* measure:
   her workbook stores it as `<column-instance derivation='Sum'
   name='[sum:Calculation_…:ok]' type='ordinal'>`, i.e. aggregation `Sum` with
   the `:ok` (ordinal) type suffix. cwtwb's field registry derives `Sum`
   instances only with the `:qk` suffix, so that exact pair is not reachable.
   Declaring the LoD a second time as `type="ordinal"` alone yields a
   `derivation="None"` `:ok` instance, which is a dimension-style binding, not
   an aggregated pill. Wrapping the LoD in `SUM()`
   (`2021 Sales (discrete) = SUM([2021 Sales])`) registers it as
   `derivation="User"` and emits `[usr:…:ok]`, which is the ordinal-aggregate
   form the author corpus also uses (22 such instances across
   `dashboards/`). This is a builder-level workaround, not an SDK change.
2. **Synchronised folded axis without `configure_dual_axis`.** The two panes
   carry *different* colour fields and one of them carries a text encoding, so
   the two-pane `configure_layered_chart(axis_shelf="columns", fold_axes=True,
   synchronized=True)` path is used instead of `configure_dual_axis`, and the
   axis fold is verified on the generated `style-rule[@element='axis']`.

No reusable SDK capability gap was found: every step maps to a public API, and
the published screenshot anomaly below is an authoring artifact rather than an
SDK problem.

## Finding: the published screenshot's labels are offset by one row

The author's published raster (`image-9.png`) prints the `% Difference` label
for a row on the row *below* it from the second row onwards: 13 of 14 shifted
labels match the next row's computed percentage exactly, and only the first row
(`Phones`, `+33%`) matches its own. The author's workbook XML, by contrast,
attaches a single `<text column="…% Difference…">` encoding to the circle pane
with no per-row offset, so the workbook itself is correct and only the exported
image is misaligned.

The verifier therefore pins the extract to the two values that are *not*
affected by the shift (the printed 2021 pill values and the 2020 dot positions,
which were read back through a fitted pixel scale of
`x = 407.35 + 0.002994 × sales` that reproduces every dot centre within 2 px)
and then checks the ordered sequence of published label values against the
computed percentages with the documented one-row shift.

## Final runtime correction
Both pane breakdowns are off; Current/Prior business dimensions enforce the current-year foreground. Live Cloud original has correctly aligned labels, superseding the archived raster caveat. 34 category-year sales agree with independent oracle; Desktop LOADED. See final visual-review and cloud-data-verification.
