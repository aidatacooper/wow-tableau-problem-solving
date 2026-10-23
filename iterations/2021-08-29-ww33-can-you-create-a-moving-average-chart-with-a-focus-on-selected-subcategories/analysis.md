# 2021-08-29-ww33-can-you-create-a-moving-average-chart-with-a-focus-on-selected-subcategories

## Problem

Lorna Brown's challenge (following the #WOW survey where table calculations were
the most requested topic) asks for a monthly moving-average trend per
Sub-Category where the reader can steer the window and focus on a handful of
Sub-Categories.

Two parameters define the window: `pPrior` (1–6, step 1, default 3) counts the
data points *including* the current month, and `pPost` (1–6, step 1, default 3)
counts the points after it. The requirement that `pPrior` include the current
value is the whole subtlety: with `pPrior = 3` only **two** prior months are
added, hence the `+1` in the second WINDOW_AVG argument.

Five small Sub-Categories are grouped into a single `Misc` line, so the chart
has 13 lines instead of 17. The article text says "3 Sub-Categories"; the
author workbook groups five (`Art`, `Envelopes`, `Fasteners`, `Labels`,
`Supplies`), which is what the shipped visualisation shows and what is rebuilt
here.

## Why the obvious approach fails

- A plain `WINDOW_AVG(SUM([Sales]), -3, 3)` is a *fixed* window: it ignores the
  parameters, so the "prior includes current" requirement cannot be expressed.
- `WINDOW_AVG(..., -[pPrior], [pPost])` would drop the current month out of the
  prior count; the author's `(-1*[pPrior])+1` is required for the worked example
  in the article (Accessories, June 2018 = mean of April…September 2018).
- Colouring the lines per Sub-Category alone cannot express "focus": the reader
  needs one control that greys everything except the chosen members, and the
  grey marks must also shrink so the focus reads instantly. That is a Set on the
  grouped dimension driving **both** Colour and Size, plus a native set control
  on the dashboard.
- The shaded background is not a simple area chart: it is the per-month
  `WINDOW_MAX([Moving Avg])` minus `WINDOW_MIN([Moving Avg])` band. Those are
  *nested* table calcs — the inner Moving Avg addresses Month of Order Date, the
  outer window addresses Sub-Category. If the outer calc is addressed by month
  instead, every month's max equals its own value and the band collapses.

## Tableau solution chain

```text
Orders (Sample - Superstore) extract (Order Date, Sub-Category, Sales)
→ pPrior / pPost integer parameters (range 1..6, step 1, default 3)
→ Sub-Category (group): categorical group folding 5 members into "Misc"
→ Moving Avg = WINDOW_AVG(SUM(Sales), (-1*pPrior)+1, pPost)  [addressed by month]
→ Window Max Avg / Window Min Avg = WINDOW_MAX/MIN(Moving Avg) [addressed by Sub-Category (group)]
→ Sub-Category (group) Set (13 members) → Colour + Size (in 1.0, out 0.2, reversed)
→ Viz sheet: Line pane on the Moving Avg axis + Area pane on the folded
  Multiple Values axis (Measure Names → Window Min Avg white, Window Max Avg #eeeeee)
→ Dashboard: checkdropdown set control + two slider parameter controls
→ observable result: 13 monthly moving-average lines with a shaded band; the
  chosen members are coloured and thick, everything else grey and thin.
```

## Required behavior

- `pPrior`/`pPost` exist as integer range parameters, min 1, max 6,
  granularity 1, value 3, and both are exposed as sliders on the dashboard.
- `Sub-Category (group)` folds exactly `Art`, `Envelopes`, `Fasteners`,
  `Labels`, `Supplies` into `Misc`, leaving 13 members.
- `Moving Avg` is the author's formula with the `+1` prior offset and is
  addressed by Month of Order Date.
- `Window Max Avg` / `Window Min Avg` wrap `[Moving Avg]` and are addressed by
  `Sub-Category (group)` with the month as nested addressing.
- The chart is a Line pane on its own axis folded with an Area pane on
  `Multiple Values`, synchronised, fold reversed so the lines sit on top.
- The set drives Colour (in-set member colours, out-of-set `#bab0ac`) and Size
  (catsize 0.2–1, reversed); the dashboard carries the set membership control.
- The band uses the white/pale-grey Measure Names palette so it paints behind
  the lines.

## Data finding: sparse Sub-Category months

Three Sub-Categories (`Bookcases`, `Copiers`, `Machines`) have no orders in some
months, so they produce no mark for those months. Tableau table calculations run
over the marks that exist, so their window averages the neighbouring months that
do have rows instead of treating the gap as a zero. The verifier models this
explicitly (597 group-month rows out of 13 x 48) because the naive dense grid
shifts every value after a gap.

## Allowed visual differences

- Fonts, padding, borders, exact zone geometry and the title block may differ.
- The author's line colours come from a "Hue Circle → Assign Palette" click; the
  per-member hex values are reproduced but are not a functional requirement.
- Mark-size interpolation of the set is reproduced as a categorical size
  interval rather than by eye.

## cwtwb baseline

cwtwb 0.29.0a1 (commit 23b1df0) covers everything the sheet needs through public
APIs:

| Need | API |
| --- | --- |
| Range parameters with step | `add_parameter(domain_type="range", min_value, max_value, granularity)` |
| Categorical group | `add_group(field, source, {"Misc": [...]})` |
| Set on the grouped field | `add_set(..., members=[...])` |
| Nested table calcs | `add_calculated_field(table_calc=...)` + `configure_layered_chart(table_calc_overrides=...)` |
| Line + Area on one folded axis | `configure_layered_chart(axis_shelf="rows", fold_axes=True, synchronized=True)` |
| Set colour and size | `set_datasource_color_palette`, `set_compound_color_palette`, `configure_worksheet_style(size_style=...)` |
| Set control on the dashboard | `add_dashboard` layout node `{"type": "set_control", "mode": "checkdropdown"}` |
| Slider parameter controls | layout node `{"type": "paramctrl", "mode": "slider"}` |

No SDK change was needed and no workaround was required for correctness: the
builder is written entirely against the public API. `cwtwb_result` is recorded as
`workaround` only because of one observable authoring constraint found while
building the compound palette:

- `set_compound_color_palette` writes the pair palette as
  `[io:Sub-Category (group) Set:nk]\n[Sub-Category (group)]`, which is exactly
  the author's own encoding key, so the in/out colouring resolves without any
  XML editing.

(There is no capability gap: the composite palette, the categorical size
interval and the set membership control all exist as public API. The case is
therefore recorded as `pass` with `functional_status: partial` only until the
Desktop gate and the Cloud render are executed by the coordinator.)
