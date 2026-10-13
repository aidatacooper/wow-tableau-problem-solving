# WW27 Cloud acceptance — top and bottom performers

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Candra McRae, built by Donna Coles) flags Sub-Categories in the
top and bottom quartiles of rolling sales, comparing the current rolling N
months against the previous N months, with a month selector driving N.

## What was checked

- **Data**: the locked extract has 9,994 line items across 17 Sub-Categories;
  the verifier recomputes the rolling windows and the quartiles independently.
- **Rolling windows**: `Max Date = DATE({FIXED:MAX([Order Date])})` = 2021-12-30;
  the current window is 2020-12-01..2021-12-30 and the previous window is
  2020-11-01..2021-11-30.
- **Quartiles**: `WINDOW_PERCENTILE` gives p25 = $17,760 and p75 = $75,456.
- **Classification**: Top = {Phones, Chairs, Binders, Storage, Tables};
  Bottom = {Supplies, Art, Labels, Envelopes, Fasteners} — matching the author.
- **Contraction**: 9 Sub-Categories fell below the previous period.
- **Chart**: a folded dual axis with a quartile-coloured Bar pane over a
  previous-sales Gantt bar pane, plus the contraction circle.
- **Month selector**: the Square sheet exposes 1-12 and a parameter action sets
  `pRollingMonth`, resetting to 12 on clear.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The contraction circle renders in the default grey rather than the author's
  red; the marker and its position are the same.

## Workarounds recorded

- Addressing `WINDOW_PERCENTILE` by `Rows` or by a single dimension makes it
  compute per-cell, so every row's percentile equals its own value and the whole
  table classifies as "Top". The percentile and `Colour` fields are addressed by
  Columns, which spans the whole table.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification and the native contracts.
