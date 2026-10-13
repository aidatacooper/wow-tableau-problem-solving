# 2021-07-08-ww27-can-you-find-the-top-and-bottom-performers

## Problem

Flag Sub-Categories whose rolling sales fall in the top or bottom quartile,
comparing the current rolling N months against the previous N months, with a
month selector driving N.

## Why the obvious approach fails

The challenge asks for statistical *quartiles*, not a `Top N`/`Bottom N` list,
and the window itself is dynamic: "current" is the maximum date in the data, the
current window is the N months ending there, and the previous window is the N
months ending one month earlier. A reference line is explicitly disallowed, so
the previous-period value must be a real mark.

The crux is the `WINDOW_PERCENTILE` addressing. The percentile fields must
compute across the whole table (addressed by the dimension that spans it), or
every row is its own window and the percentile collapses to the row's own value
— which makes every row "Top". The author addresses them by Columns; the replica
uses the same addressing so the classification matches the independent oracle.

## Tableau solution chain

```text
data (Order Date, Sub-Category, Sales)
→ Max Date = DATE({FIXED:MAX([Order Date])})
→ pRollingMonth (integer, default 12, driven by a parameter action)
→ Current Rolling Sales = sales in [DATETRUNC('month',[Max Date])-N, [Max Date]]
→ Prev Month = DATEADD('month', -1, [Max Date])
→ Previous Rolling Sales = sales in [DATETRUNC('month',[Prev Month])-N, [Prev Month]]
→ Difference = SUM(Current) - SUM(Previous)
→ 25th/75th Percentile = WINDOW_PERCENTILE(SUM([Current Rolling Sales]), .25/.75)
→ Colour = Top / Bottom / Middle by those thresholds
→ Sales Contraction Indicator = '●' when the difference is negative
→ Chart: Sub-Category bars coloured by Colour over a previous-sales Gantt bar,
  with a hidden Sub-Category row carrying the contraction circle
→ Month Selector: MONTH([Order Date]) squares driving pRollingMonth
```

## Required behavior

- `ww27-rolling-windows`: the current and previous rolling windows are the
  parameterised `DATEADD`/`DATETRUNC` ranges off `Max Date` and `Prev Month`.
- `ww27-quartile-classification`: `Colour` classifies each Sub-Category from the
  `WINDOW_PERCENTILE` thresholds.
- `ww27-contraction-indicator`: `Sales Contraction Indicator` marks the rows
  whose current sales fell below the previous period.
- `ww27-chart`: the chart is a folded dual axis with a quartile-coloured Bar
  pane over a previous-sales Gantt bar pane.
- `ww27-month-selector`: the Month Selector sheet exposes 1-12 and a parameter
  action sets `pRollingMonth`, resetting to 12 on clear.
- `ww27-quartile-values`: the oracle confirms the top/bottom/middle membership
  for the default 12-month window.

## Allowed visual differences

- Fonts, padding and the exact stroke widths differ.
- The contraction circle renders in the default grey rather than the author's
  red; the marker and its position are the same.

## cwtwb baseline

Tested with the released SDK `0.27.1` (`4cd2c61c`).

- `add_calculated_field(..., table_calc="Columns")` addresses the percentile
  fields across the whole table; addressing them by `Rows` or by a single
  dimension makes `WINDOW_PERCENTILE` compute per-cell and misclassifies every
  row as "Top".
- `configure_layered_chart(axis_shelf="columns", fold_axes=True,
  synchronized=True)` builds the two overlaid panes; the `Rows` shelf carries
  the hidden `Sub-Category`, the contraction indicator and the visible copy.
- `add_dashboard_action(action_type="parameter", clear_behavior="set-value",
  clear_value="i:12")` reproduces the author's reset-on-clear behaviour.
