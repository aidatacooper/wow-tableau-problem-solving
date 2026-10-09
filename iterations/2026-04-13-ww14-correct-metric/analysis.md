# 2026-04-13-ww14-correct-metric

## Problem

A discount average is easy to compute and easy to get wrong. When an order has
several lines with different quantities, the plain `AVG([Discount])` weights
every *line* equally, but the business question — "what discount did we
actually give, per item?" — needs a *quantity*-weighted average. The user needs
to see, per order, both numbers and which orders disagree.

## Why the obvious approach fails

`AVG([Discount])` in Tableau is `SUM([Discount]) / COUNT(rows)`. It ignores
`Quantity`, so a 9-item line at 80% discount counts the same as a 2-item line
at 20%. On Sample-Superstore the two metrics diverge on a large share of
orders, so a dashboard built on `AVG` alone answers the wrong question while
looking perfectly correct. The challenge is to expose the difference rather
than hide it.

## Tableau solution chain

```text
data domain (Sample - Superstore lines: Order ID, Order Date, Category,
             Quantity, Discount)
→ calculations
    Weighted Avg        = SUM([Discount]*[Quantity]) / SUM([Quantity])
    Difference from correct metric
                        = ABS([Weighted Avg] - AVG([Discount]))
    Is difference?      = ROUND([Difference from correct metric],3) <> 0
→ worksheets
    Simple Avg    scatter: AVG(Discount) x AVG(Quantity), detail = Order ID
    Weighted Avg  scatter: Weighted Avg   x AVG(Quantity), detail = Order ID
    Order Details detail sheet used as a Viz in Tooltip
→ dashboard/actions
    both scatters on one dashboard + a highlight action on select
→ observable result
    each dot is an order; orders where the simple and weighted discount
    differ are coloured by Is difference?
```

Filter chain (author, and reproduced): restrict `Order Date` to the last three
months of the extract — Oct/Nov/Dec 2025 — and keep only marks with
`0 <= Difference from correct metric <= 1/6`.

Worked example from the article: five lines, discounts 20/80/80/80/20 % with
quantities 2/3/5/9/7 →
`(2*0.2 + 3*0.8 + 5*0.8 + 9*0.8 + 7*0.2) / 26 = 15.4 / 26 = 59.2%`, whereas
the simple average of the same five lines is 56%.

## Required behavior

- `Weighted Avg` equals `SUM(Discount*Quantity)/SUM(Quantity)` — verified
  against an independent Hyper aggregate, not against the author workbook.
- `Difference from correct metric` equals `ABS(Weighted Avg - AVG(Discount))`.
- `Is difference?` is `ROUND(difference,3) <> 0`, so sub-0.001 float noise does
  not paint an order as different.
- Both scatter sheets plot one mark per `Order ID` and colour by
  `Is difference?`.
- The `Simple Avg` sheet places `AVG(Discount)` on columns; the `Weighted Avg`
  sheet places `Weighted Avg` on columns. Both place `AVG(Quantity)` on rows.
- The dashboard shows both sheets and carries a select (highlight) action.

## Allowed visual differences

- Fonts, padding, borders, decoration, and the exact "label only when
  highlighted" behaviour may differ; they do not change the answer.
- The author's `.twb` uses opaque internal field names
  (`Calculation_1755428175818754`, …). The replica uses readable names; the
  formulas are what must match.

## cwtwb baseline

Built with the released cwtwb pinned in `requirements.txt`. The case needs
only public APIs: `set_hyper_connection`, `add_calculated_field`,
`add_worksheet`, `configure_chart`, `configure_custom_tooltip` (Viz in
Tooltip), `configure_worksheet_style`, `add_dashboard`,
`add_dashboard_action(action_type="highlight")`. No reusable capability gap was
found; any gap discovered here would be filed separately, not worked around
silently.
