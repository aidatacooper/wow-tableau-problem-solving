# 2021-04-01-ww13-sub-orders-profitable

## Problem

Week 13 asks for a modified mekko (marimekko / mosaic) chart on the Superstore
dataset:

- bar **height** = the percentage of a Sub-Category's orders that are
  profitable; the lower bar shows one minus that percentage;
- bar **width** = the Sub-Category's share of total sales;
- bars ordered by the profitable percentage, then by total sales.

The subtlety is the grain. A single order can contain product lines from several
Sub-Categories, so an order is only "profitable for a Sub-Category" when the
total profit of that Sub-Category's lines on the order is positive — not when
any individual product line is profitable.

## Why the obvious approach fails

- **A per-row profit test is the wrong grain.** Counting rows with
  `[Profit] > 0` counts product lines, not orders, and disagrees with the
  challenge for most Sub-Categories (for example Machines is 63% at the order
  grain but a different figure per row).
- **The Sub-Category dimension cannot position the bars.** Because each bar has
  a data-driven width, the x-axis has to be the cumulative share of sales; the
  Sub-Category is only a detail, so a normal dimension shelf would give every
  bar equal width.
- **Sorting by a table-calculation pill is not possible.** The order depends on
  the profitable percentage and sales, but once the Sub-Category leaves the
  shelves the built-in sort options no longer apply. The article builds an
  explicit string `Sort` key (`STR(ROUND([Profitable Orders],2)) + "-" +
  STR(ROUND(SUM([Sales])/1000000,2))`) and sorts the detail dimension by it.
- **Two heights need two axes.** Profitable and non-profitable percentages
  cannot share one continuous axis; they are stacked around zero, which needs a
  second pane with a reversed axis and a constant zero reference line.

## Tableau solution chain

```text
Superstore extract (Order ID, Segment, Sub-Category, Sales, Profit)
→ order-grain profitability:
     Order Is Profitable = IIF({FIXED [Order ID],[Sub-Category]: SUM([Profit])}>0,1,0)
     Count Orders        = COUNTD([Order ID])
     Profitable Orders   = SUM([Order Is Profitable])/[Count Orders]      (p0%)
     Non Profitable Orders = 1 - [Profitable Orders]                       (p0%)
→ mekko geometry:
     % of Total Sales            = SUM([Sales])/TOTAL(SUM([Sales]))
     % Total Sales Cumulative    = RUNNING_SUM([% of Total Sales])
                                   (addressed by Sub-Category)
     Sort = STR(ROUND([Profitable Orders],2)) + "-" + STR(ROUND(SUM([Sales])/1000000,2))
→ one worksheet, two stacked panes sharing the row axis:
     pane 1  Profitable Orders      (normal axis)
     pane 2  Non Profitable Orders  (reversed axis)
     both: Bar mark, Size = % of Total Sales (fixed, right-aligned),
           Detail = Sub-Category, Colour = Measure Names
→ constant zero reference line draws the black separator
→ computed sort on Sub-Category by Sort descending
→ Segment filter (Consumer, Corporate, Home Office)
→ observable result: variable-width columns whose pink height is the profitable
  order share and grey height the remainder, ordered by profitability then sales.
```

## Required behavior

- An order counts as profitable for a Sub-Category when the summed profit of
  that Sub-Category on the order is positive (`FIXED` LoD at that grain).
- The upper bar height is the profitable-order percentage and the lower bar is
  its complement, so the two stack to the full column.
- Each column's width is the Sub-Category's share of total sales, and the bars
  are laid out on a cumulative-sales axis starting at −0.05.
- Columns are ordered by the profitable percentage descending, then by sales
  descending.
- A black constant-zero line separates the profitable and non-profitable halves.

## Allowed visual differences

- Fonts, padding, label placement and the exact pink/grey palette are
  decorative.
- The author's `Data` debugging sheet is not reproduced.
- Axis titles and the footer text zone differ.

## cwtwb baseline

`cwtwb 0.27.1` (commit `4cd2c61c`) built the whole solution with public APIs
only:

- `add_calculated_field` for the `FIXED` LoD and the table calculations;
- `configure_layered_chart` with `axis_shelf="rows"`, `fold_axes=True` and two
  panes for the stacked halves; each pane carries a `size` encoding and a
  `mark_sizing` dictionary (`marks-scaling-on`, `mark-alignment-right`) that
  reproduces the author's fixed-width marks;
- `table_calc_overrides` for the `TOTAL` / `RUNNING_SUM` addressing;
- a reversed pane axis encoding via `configure_worksheet_style(axis_style=...)`
  for the lower half;
- `set_datasource_color_palette("Measure Names", ...)` for the pink/grey pair;
- `add_reference_line(formula="constant")` plus
  `configure_reference_line_style` for the zero separator;
- `configure_layered_chart(sort_mode="computed", sort_field="Sub-Category",
  sort_descending="Sort")` for the detail-dimension sort.

One implementation note, not a reusable gap: `configure_dual_axis` routes the
sort through `_add_shelf_sort`, which requires the sort field to sit on the row
shelf; the author's `Sort` key is only on Detail. `configure_layered_chart`
supports a Detail-bound computed sort, so the case uses it. No workaround and no
capability gap, so `cwtwb_result` is `pass`.
