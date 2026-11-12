# 2022-01-14-ww02-can-you-build-a-weekly-year-over-year-line-chart

## Problem

Leadership wants this year's weekly sales next to the two prior years, with the
year-over-year change at each week. The trap is that "the same week" is not the
same date: 4 Jan 2021, 6 Jan 2020 and 7 Jan 2019 are all the *first Monday* of
their year, so three calendar years have to be plotted on one shared axis
before anything can be compared.

## Why the obvious approach fails

- `YEAR([Order Date])` splits a week that crosses 31 December: the week of
  30 Dec 2019 – 5 Jan 2020 would be counted as part of both 2019 and 2020.
  The author's answer is to group by the year of the *week start*, expressed as
  a signed offset from "today".
- Three separate date axes cannot be compared, so the dates must be re-based
  onto one year. `MAKEDATE(2021, MONTH(d), DAY(d))` keeps month and day but
  drops the weekday: 2019-01-07 becomes Thursday 7 Jan 2021 and 2020-01-06
  becomes Wednesday 6 Jan 2021, while 2021-01-04 stays Monday 4 Jan. The three
  years therefore do **not** line up until the rebased date is truncated back
  to its week.
- That truncation is also what makes the year-over-year calculation possible.
  A table calculation computes along an addressing direction and within the
  partition defined by every *other* dimension in the view. Only when all three
  years' marks share one axis position does a single partition contain the
  three values that "compare to the previous year" needs. Plotting exact
  rebased dates instead puts each year at its own position, and the same
  calculation silently degrades into week-over-week growth.
- The dataset ends on 28 Nov 2021, so the challenge's "exclude the incomplete
  week" rule (today = 1 Dec 2021, a Wednesday) removes nothing here. The filter
  is still implemented because it is the specified behaviour, and because
  changing the `Today` parameter is the whole point of making it a parameter.

## Tableau solution chain

```text
data domain (one row per order: Sales, Order Date)
→ calculations
    Order Date Week Start = DATE(DATETRUNC('week', [Order Date]))     -- Monday
    Order Date Week End   = DATE(DATEADD('day', 6, [Order Date Week Start]))
    Year Group            = YEAR([Today]) - YEAR([Order Date Week Start])
    Date to Plot          = DATE(DATETRUNC('week',
                              MAKEDATE(2021, MONTH(week start), DAY(week start))))
    Core Data to Include  = [Order Date Week End] < [Today]
                            AND YEAR([Order Date Week Start]) >= YEAR([Today]) - 2
    % Sales Diff          = (ZN(SUM([Sales])) - LOOKUP(ZN(SUM([Sales])), 1))
                            / ABS(LOOKUP(ZN(SUM([Sales])), 1))
    % Sales Diff +ve/-ve  = the sign split, formatted ▲0.0%;▼0.0%
    TOOLTIP: Label YoY%   = IF NOT(ISNULL([% Sales Diff])) THEN 'YoY%:' END
→ parameter
    Today = #2021-12-01#          (the challenge's fixed "today")
→ worksheet
    Date to Plot on Columns (continuous date), SUM(Sales) on Rows,
    Year Group on Colour (0/1/2 → green/blue/grey), Core Data to Include = true
    filter, percentage difference addressed by Year Group
→ dashboard
    1100 × 800, the sheet plus the challenge title key and credits
→ observable result
    three weekly lines over one Jan–Dec axis, coloured Current / Previous /
    2 Yrs Ago, with a tooltip that shows the week ending date and the YoY%
    change, and no YoY% on the oldest line
```

The colour key is not a legend: the author puts "CURRENT | PREVIOUS |
2 YRS AGO" into the worksheet title as three coloured runs, and orders the
colour members Current → Previous → 2 Yrs Ago with a manual sort.

## Required behavior

- Every order date is bucketed to the Monday–Sunday week that contains it, and
  the datasource starts weeks on Monday.
- `Year Group` is a signed offset from the `Today` parameter, so the week of
  30 Dec 2019 stays in one group even though it crosses into 2020.
- All three years are plotted on one continuous 2021 axis, and the three years'
  marks for a given week share one axis position.
- `% Sales Diff` compares a week with the *same week of the previous year*, and
  the oldest line has no value.
- The tooltip shows the week ending date (`mmm dd`), the period name, sales
  (`$#,##0`) and the YoY% change coloured green for positive and red for
  negative; the "YoY%:" label is suppressed when there is no value.
- `Today = #2021-12-01#` and the completeness filter are parameter-driven.

## Observed data facts

Recomputed from `inputs/Sales Growth (2022_01_12_WW01_Superstore Sales
Growth).hyper` (7,499 rows, Order Date 2019-01-09 … 2021-11-28):

| Year group | Weeks | First week start | Last week start |
| --- | --- | --- | --- |
| Current (0) | 47 | 2021-01-04 | 2021-11-22 |
| Previous (1) | 52 | 2020-01-06 | 2020-12-28 |
| 2 Yrs Ago (2) | 52 | 2019-01-07 | 2019-12-30 |

- These are exactly the endpoints the author's article names ("7 Jan 2019,
  6 Jan 2020 and 4 Jan 2021" first, "30 Dec 2019 … 22 Nov 2021" last).
- 52 distinct axis positions, 47 of which carry all three years.
- The extract contains no 2018 row (it starts 9 Jan 2019) and no order after
  28 Nov 2021, so both halves of `Core Data to Include` are no-ops on this
  dataset. They are still implemented, and the verifier asserts the no-op so a
  changed dataset cannot quietly start plotting a partial week.

## Allowed visual differences

- The x-axis tick labels are anchored differently: the author's continuous
  *week-truncated* date pill ticks on week starts (`11 Jan, 08 Feb, …`), the
  replica's continuous exact-date axis ticks on month starts (`01 Jan,
  01 Feb, …`). Both are `dd mmm` over the same 52 positions; the axis scale
  differs by 0.3% (≈3 px at 2200 px wide) because Tableau pads a day-grain
  continuous axis differently from a week-grain one.
- The title renders in Tableau's default title font instead of Tableau Medium,
  because cwtwb's rich-title writer has no `fontname` attribute.
- Fonts, padding and the dashboard footer link text may differ.

## cwtwb baseline

Built with the released cwtwb in this environment (0.29.0a2) using only public
APIs: `set_hyper_connection`, `set_date_options`, `add_parameter`,
`add_calculated_field` (with `table_calc` addressing), `add_worksheet`,
`configure_chart` (filters, tooltip shelf, `table_calc_overrides`),
`set_datasource_color_palette`, `configure_worksheet_style`,
`set_field_format`, `configure_custom_tooltip`, `set_worksheet_rich_title`,
`add_dashboard`.

`cwtwb_result: workaround`. Two reusable gaps were hit; both are worked around
inside the case, and neither changes what the reader sees except the axis tick
anchor:

1. **No continuous week-truncated date grain.** Tableau's `twk` column instance
   (`derivation="Week-Trunc"`) is the author's date pill and is what aligns the
   three years on one axis position. cwtwb exposes `DAYTRUNC/MONTHTRUNC/
   QUARTERTRUNC/YEARTRUNC` but no `WEEKTRUNC`, so the truncation is folded into
   the `Date to Plot` calculation and the shelf binds a continuous exact date.
   The cost is the tick anchor and a 0.3% axis-scale difference.
2. **No dimension member aliases.** The author aliases the `Year Group`
   members (`0 → Current`, `1 → Previous`, `2 → 2 Yrs Ago`). cwtwb aliases
   parameters and Measure Names only, so the same three labels are produced by
   a `Period Label` string calculation used on the tooltip. The colour legend
   is not displayed on the dashboard, so the numeric members are invisible.

A third, smaller gap already documented by other cases: `set_worksheet_rich_title`
drops `fontname`.

Note on the baked percentage difference: Tableau stores a referenced
calculation's addressing in the nested `<table-calc field=...>` metadata of the
referencing instance. With Tableau's default `Rows` addressing on `% Sales
Diff` the LOOKUP walks along the date axis and returns week-over-week growth
(`-72.6%` where the author shows `+27.8%`). The builder therefore gives
`% Sales Diff` an explicit `ordering-field` of `Year Group`, which the nested
metadata inherits.
