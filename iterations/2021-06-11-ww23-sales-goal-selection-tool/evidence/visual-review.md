# WW23 Cloud acceptance — Sales Goal Selection Tool

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Ann Jackson, rebuilt by Donna Coles) computes two different
year-end sales goals and lets the user toggle each sub-category between them,
then aggregates the mixed goals into the three headline BANs.

## What was checked

- **Data**: the locked extract has 9,994 rows; the verifier recomputes every
  sub-category aggregate in Python from the extract itself.
- **Goal arithmetic**: `Same Pace Goal` and `LY + Percent Increase Goal` match
  the article's formulas, and the DATEDIFF day counts are leap-year safe
  (160 days so far / 365 in 2021).
- **Mixed aggregation**: `YEAR-END GOAL Per Sub Cat` branches on
  `ATTR([Use Last Year With Increase])`; `WINDOW_SUM` + `INDEX() <= 1` produce
  the single-row BAN strip.
- **BANs**: SALES YTD $216,042, SALES LY YTD $199,947, YEAR-END GOAL $546,803
  with the author's four-member set — all three match the article's screenshot.
- **Chart**: Measure Values bars (SALES YTD orange, SALES LY YTD grey) with the
  black Gantt goal tick, the `Value to Goal` / `% of Goal` text panes and the
  set-coloured circles, all sharing one folded column axis.
- **Toggle**: the `Use Last Year With Increase` set starts with Accessories,
  Copiers, Machines and Phones, and the two `edit-group-action` set actions add
  (click) and remove (tooltip link) members.
- **Layout**: 1200×800 dashboard with the title band, BAN strip, chart and the
  two-colour footer legend.

## Accepted visual differences

- Fonts, padding and exact stroke widths differ.
- The article's mid-build screenshots show the set at other memberships
  (Phones only → $513,833; none → $492,845); the replica reproduces the
  author's shipped four-member default of $546,803, and the oracle confirms the
  other totals are reachable through the same formulas.
- The chart's per-pane column widths are Tableau's automatic layout, so the
  gap between the bar block and the text panes differs slightly.

## Workarounds recorded

- A quantitative filter with both `min=1` and `max=1` on `INDEX()` did not
  collapse the BANs to one row on Cloud; only the upper bound (`max=1`) is
  written, matching the author's workbook.
- The customized labels drop literal angle brackets because a literal `<` run
  plus a field run renders as `<<field>>`.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses
the article's written specification, the article's build screenshots and the
native workbook contracts.
