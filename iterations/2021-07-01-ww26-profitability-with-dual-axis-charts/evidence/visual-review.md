# WW26 Cloud acceptance — profitability with dual axis charts

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Luke Stanke, built by Donna Coles) asks for a Pareto view: the
cumulative-profit curve against the cumulative percentage of orders, with
per-order sales bars behind it on an unsynchronised dual axis, plus a subtitle
reporting the share of profitable orders and the potential profitability
decrease.

## What was checked

- **Data**: the locked extract has 9,994 line items across 5,009 orders; the
  verifier aggregates them to one profit per order and recomputes the whole
  table-calculation chain independently.
- **Cumulative counts**: `Count Orders = COUNTD([Order ID])` with
  `RUNNING_SUM`/`WINDOW_SUM` for the cumulative and total counts.
- **Cumulative percent**: `Cumulative % of Total Orders` reaches exactly 100%.
- **Cumulative profit**: the profit running sum, whose final value is the total
  profit ($286,397).
- **Profit colour**: `Profit is +ve = SUM([Profit]) > 0` colours the
  cumulative-profit line.
- **Subtitle measures**: the marker row (index 3,970) yields
  `% of Total Profitable = 79%` and
  `Potential Profitability Decrease = 33%`, matching the author.
- **Dual axis**: a folded, **unsynchronised** axis with a Line pane over a Bar
  pane, Order ID on Detail with a profit-descending computed sort.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The replica does not reproduce the author's exact teal/orange pair; the
  article's stated `Profit is +ve` split is what matters.

## Workarounds recorded

- Passing `table_calc_overrides` for these fields replaces the auto-generated
  nested `<table-calc>` dependency metadata. Without it the cumulative curve
  collapses to 100% and the subtitle reads `397100%` / `0%`. Leaving the
  overrides unset lets the builder emit the correct nested metadata.

## Not claimed

This is not a pixel match, and no browser interaction is claimed. The author's
published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification, the author's Cloud render and the native
contracts.
