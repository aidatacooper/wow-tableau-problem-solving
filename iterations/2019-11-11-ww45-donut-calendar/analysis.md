# 2019-11-11-ww45-donut-calendar

## Problem

Track daily order fulfilment rates across regions for the trailing 7 days relative to a configurable report date (November 6, 2019). The visualization presents a calendar matrix of regions (rows) and dates (columns) using donut charts to display % of shipped orders, transitioning into green checkmark badges when a region-day achieves 100% fulfilment.

## Why the obvious approach fails

A basic bar or table chart obscures the proportional completion rate within each day-region combination. Conversely, standard pie charts do not offer an inner label area. Furthermore, handling days with 100% fulfilment versus partial fulfilment requires distinct conditional representations (donut progress ring vs solid green completed badge with checkmark).

## Tableau solution chain

```text
Superstore orders (Extract)
→ Report Date parameter (#2019-11-06#)
→ Date filtering ([Order Date] in trailing 7 days of Report Date)
→ Fulfilment calculations (Has Shipped?, % Shipped, Fully Shipped?, LABEL %)
→ Dual-axis worksheet (Pie mark for shipped proportion + inner Circle mark for completion label)
→ Dashboard matrix (Regions on Rows, Order Dates on Columns)
→ Observable donut calendar with conditional completion badges
```

## Required behavior

- Trailing 7-day window scoped to `Report Date` (#2019-11-06#).
- 4 Regions mapped along the vertical row axis: Central, East, South, West.
- Trailing order dates mapped along the horizontal column axis.
- Dual-axis donut charts:
  - Base mark: Pie chart showing shipped orders vs unfulfilled orders.
  - Overlay mark: Inner circle mark creating the donut hole, colored white for partial completion or green for 100% completion.
- Dynamic label:
  - Displays percentage string (e.g. `67%`, `80%`) when partially shipped.
  - Displays checkmark (`✓`) when fully shipped (100%).
- Single unified dashboard displaying the calendar grid.

## Allowed visual differences

- Exact circle diameter, background grid shading, and font hierarchy may differ slightly from the original publication.
- Background image watermark techniques (from the original author's single-sheet workaround for missing dates) are replaced by standard clean dual-axis marks.

## cwtwb baseline

The released `cwtwb` (version 0.27.0) provides native support for:
- Hyper extract connection
- Date parameter creation
- Calculated fields with conditional logic and aggregations
- Synchronized dual-axis chart construction (`configure_dual_axis` with `Pie` and `Circle` marks)
- Categorical filter application
- Dashboard composition
