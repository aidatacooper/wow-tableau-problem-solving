# WW20 Cloud acceptance — compare same day to a selected date

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Lorna Brown, built by Donna Coles) asks for a BAN comparing the
selected day's sales to the *equivalent weekday* one year / one month / one week
earlier, a line chart showing the two days as labelled line ends, a click-to-set
date action and a reset button — with no LoDs and no table calculations.

## What was checked

- **Data**: the locked extract has 9,994 rows across 1,236 distinct order dates;
  the verifier recomputes the per-day sums independently
  (`evidence/functional-verification.json`).
- **Equivalent-day logic**: the verifier re-implements `DATEADD`, `DATEPART`,
  `DATETRUNC` and `MONTH` in Python and probes the leap-year branch and the
  missing-5th-occurrence fallback; the workbook formula chain matches.
- **Default values**: for 18 May 2021 the BAN shows `$1,831` selected,
  `$1,582` compared (Tuesday 19 May 2020) and `▲15.7%`, matching the article.
- **BAN contract**: `MIN(1)` bar, fixed 0..1 column axis, coloured by
  `% Difference` with the author's 24-swatch diverging palette, and the
  multi-line label composed from the selected date, selected sales, difference,
  compared sales and `(pComparison: Compare Date)`.
- **Chart contract**: Sales by exact Order Date filtered to `Dates To Show`, with
  `Selected Date Sales`, `Compared Date Sales` and `AVG(Minus 500)` on a shared
  second axis and the value label pinned to the -500 points.
- **Interaction contract**: two native `edit-parameter-action`s (chart click and
  reset) plus a `True → False` filter action.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The chart's dual axis keeps its default titles off; the author hides the
  headers entirely. The plot and the two labelled line ends are the same.
- The Reset button renders as a black square with the 'Reset' label.

## Not claimed

This is not a pixel match, and no browser click/hover execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification and the native contracts.
