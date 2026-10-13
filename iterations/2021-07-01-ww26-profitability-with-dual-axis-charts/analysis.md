# 2021-07-01-ww26-profitability-with-dual-axis-charts

## Problem

Recreate Luke Stanke's Pareto chart: order IDs sorted by profit descending, a
cumulative-profit line coloured by whether each order was profitable, and a
sales bar behind it on an **unsynchronised dual axis**. The subtitle reports the
share of orders that were profitable and how much the unprofitable orders cut
potential profitability.

## Why the obvious approach fails

1. **Everything is a table calculation.** `Cumulative Profit`,
   `Cumulative Order Count`, `Total Order Count`, `Cumulative % of Total Orders`,
   `Profitable Marker`, `Total Cumulative Profit` and
   `Potential Profitability Decrease` are all running/window calculations whose
   results depend entirely on their *addressing* (compute-using) and on the
   order of the marks (profit descending).
2. **Nested table calculations.** `Cumulative % of Total Orders` divides one
   running total by a window total; the author addresses the running count by
   **Columns** and the total by **Rows**, and the ratio by **Rows**. Getting any
   one of those wrong collapses the curve.
3. **The x axis is a table-calc field, not a dimension.** The Pareto needs the
   cumulative percent on columns and the cumulative profit on rows, with Order
   ID only as a detail-level field, sorted by `SUM(Profit)` descending.
4. **Two axes with different scales.** Cumulative profit (~-300K to +400K) and
   order size (~0 to 20K) share the view but not the scale, so the axes must be
   unsynchronised.

## Tableau solution chain

```text
data (Order ID, Sales, Profit)
→ Count Orders = COUNTD([Order ID])
→ Cumulative Order Count = RUNNING_SUM([Count Orders])   [compute using Order ID]
→ Total Order Count = WINDOW_SUM([Count Orders])         [compute using Order ID]
→ Cumulative % of Total Orders = [Cumulative Order Count]/[Total Order Count]
→ Cumulative Profit = RUNNING_SUM(SUM([Profit]))         [compute using Order ID]
→ Profit is +ve = SUM([Profit]) > 0
→ Profitable Marker = LOOKUP([Profit is +ve],-1) AND NOT([Profit is +ve])
→ % of Total Profitable = WINDOW_MAX(IF [Profitable Marker] THEN [Cumulative %] END)
→ Total Cumulative Profit = WINDOW_MAX(IF LAST()=0 THEN [Cumulative Profit] END)
→ Potential Profitability Decrease =
      WINDOW_MAX(IF [Profitable Marker] THEN
                 ([Cumulative Profit]-[Total Cumulative Profit])/[Cumulative Profit] END)
→ Viz: Order ID on Detail (sorted by Profit desc), Cumulative Profit + SUM(Sales)
   on an unsynchronised dual row axis, Cumulative % of Total Orders on columns,
   a coloured line pane over a grey bar pane
→ observable result: a Pareto curve rising to ~79% profitable before the
   unprofitable orders drag cumulative profit down ~33%
```

## Required behavior

- One mark per order, ordered by profit descending.
- Cumulative profit accumulates per order and the line is coloured by whether
  that order was profitable.
- Cumulative % of total orders rises to 100%.
- The subtitle reports the profitable share (~79%) and the potential
  profitability decrease (~33%).

## Allowed visual differences

- Fonts, colours, bar width and the exact subtitle wording may differ.

## cwtwb baseline

**Blocked.** The released SDK (0.27.1) can author every calculated field and the
dual-axis layout, and the workbook loads in Tableau Desktop, but the nested
table-calculation addressing does not survive: the `% of Total Orders` field
renders 100% for every mark instead of accumulating, so the Pareto collapses to
a single vertical line. The builder emits `<table-calc ordering-type="Field"
ordering-field="...Order ID"/>` on the running-total instances, but the ratio
field's own `Rows` addressing does not re-partition as the author's workbook
does. This is a reusable capability gap in table-calc addressing for combined
(running ÷ window) calculations.
