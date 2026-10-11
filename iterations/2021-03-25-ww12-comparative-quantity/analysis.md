# 2021-03-25-ww12-comparative-quantity

## Problem

Week 12 asks for a two-panel "Comparative Quantity Analysis" by Sub-Category on
the Superstore dataset (the version that carries a **Manufacturer** field):

- left panel: the average quantity sold per Sub-Category, **inclusive of
  manufacturer**;
- right panel: the **variance** between each Sub-Category's average and the
  average of one *selected* Sub-Category;
- clicking a Sub-Category re-selects the comparison baseline;
- the challenge explicitly forbids `FIXED` LoDs and wants `INCLUDE`/`EXCLUDE`
  expressions to carry the work.

The business question is "how does each Sub-Category's ordering quantity compare
with the one I care about right now?", where the benchmark is chosen by clicking
rather than by editing a filter.

## Why the obvious approach fails

- **A plain `AVG([Quantity])` is wrong.** It averages individual order lines, so
  a manufacturer with many small orders dominates one with a few large orders.
  The article's metric is the total quantity sold per Sub-Category divided by
  the number of *distinct manufacturers*: `SUM(Quantity)/COUNTD(Manufacturer)`.
  That is exactly the `{INCLUDE [Manufacturer] : SUM([Quantity])}` grain.
- **A `FIXED` LoD is forbidden** by the challenge. `{FIXED [Sub-Category] :
  SUM([Quantity])}` would give the total, not the per-manufacturer average, and
  would also violate the "no FIXED" rule.
- **A parameter alone does not broadcast the value.** Marking the selected row
  with `IF [Sub-Category] = [pSelectedSubCat] THEN [Avg] END` produces a value on
  one row and nulls elsewhere. The benchmark has to be *spread across every row*
  so the variance can be computed per row. The table-calculation solution uses
  `WINDOW_MAX` for this; the LoD solution uses
  `{EXCLUDE [Sub-Category], [Is Selected Sub Cat] : AVG(...)}`, which is the
  point of the exercise.
- **Two measures on one axis are not the same as two panels.** Stacking the
  average and the variance on a single continuous axis would force both into a
  shared domain and destroy the independent scales the challenge's side-by-side
  comparison needs.

## Tableau solution chain

```text
Superstore (with Manufacturer) extract
→ pSelectedSubCat parameter (string, default "Fasteners")
→ INCLUDE LoD grain:
     Qty Inc Manufacturer      = {INCLUDE [Manufacturer] : SUM([Quantity])}
     Avg Qty Inc Manufacturer  = AVG([Qty Inc Manufacturer])
→ selection flag:
     Is Selected Sub Cat       = [Sub-Category] = [pSelectedSubCat]
→ selected-subset LoD:
     Selected Qty              = IF [Is Selected Sub Cat] THEN [Quantity] END
     Selected Qty Inc Manufacturer
                               = {INCLUDE [Manufacturer] : SUM([Selected Qty])}
     Overall Selected Qty Inc Manufacturer
                               = {EXCLUDE [Sub-Category], [Is Selected Sub Cat]
                                  : AVG([Selected Qty Inc Manufacturer])}
→ comparison:
     Variance                  = AVG([Qty Inc Manufacturer])
                                 - MIN([Overall Selected Qty Inc Manufacturer])
     TOOLTIP Variance          = ABS([Variance])
     TOOLTIP more or less      = IF [Variance] <= 0 THEN 'less' ELSE 'more' END
→ one worksheet, two panes side by side on the column axis:
     pane 1  Avg Qty Inc Manufacturer   (colour by Is Selected Sub Cat)
     pane 2  Variance                   (colour by Variance, ~75% opacity)
→ dashboard with a parameter action (click Sub-Category → pSelectedSubCat)
  plus an "Unhighlight" filter action mapping True → False
→ observable result: the selected Sub-Category turns teal in the left panel and
  the right panel re-reads every variance against it.
```

## Required behavior

- Every Sub-Category is one bar on the shared row axis, sorted by the average
  quantity descending, in both panels.
- The average quantity uses the manufacturer-inclusive grain, not raw order
  rows: it equals `SUM(Quantity)/COUNTD(Manufacturer)` for each Sub-Category.
- The variance for a Sub-Category is its average minus the average of the
  currently selected Sub-Category, and is zero for the selected row.
- Selecting a Sub-Category bar sets `pSelectedSubCat`, which recolours the left
  panel and recomputes the right panel.
- No `FIXED` LoD appears anywhere in the workbook.

## Allowed visual differences

- Fonts, padding, borders, gridline visibility and the exact diverging palette
  are decorative.
- The author's `Data` debugging sheet is not reproduced; the published view is
  the single dashboard sheet.
- The exact header/footer text zones are approximated.

## cwtwb baseline

`cwtwb 0.27.1` (commit `4cd2c61c`) built the whole solution with public APIs
only:

- `add_parameter` (string, unconstrained domain) for `pSelectedSubCat`;
- `add_calculated_field` for every LoD, selection and tooltip expression —
  `{INCLUDE ...}` and `{EXCLUDE ...}` both serialize and validate;
- `configure_layered_chart(axis_shelf="columns", fold_axes=False)` places the
  two measures on the column axis as **two side-by-side panes** of one
  worksheet, which is the author's layout. With `fold_axes=True` the same
  builder produced a stacked/overlaid column instead, so the fold flag is the
  meaningful switch for "side by side";
- `configure_custom_tooltip` for the per-pane rich tooltips;
- `configure_worksheet_style` for the continuous diverging variance palette;
- `add_dashboard_action(action_type="parameter")` for the click-to-compare
  action and `action_type="filter"` with `field_mappings={"True": "False"}` for
  the author's "Unhighlight" behaviour.

No workaround was required and no reusable capability gap was found, so
`cwtwb_result` is `pass`.
