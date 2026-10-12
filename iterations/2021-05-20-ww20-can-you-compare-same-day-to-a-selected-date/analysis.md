# 2021-05-20-ww20-can-you-compare-same-day-to-a-selected-date

## Problem

Given a user-selected date and a comparison mode, show that day's sales against
the sales of the *equivalent day* — the same weekday one year ago, one month ago,
or one week ago — as a percent difference BAN plus a line chart that shows the
two days' sales as labelled points at the ends of the range. Clicking a point on
the line chart must re-select the date, and a reset button must return the
dashboard to 18 May 2021.

## Why the obvious approach fails

Tableau's built-in relative-date filters compare the *same calendar date* (18 May
2021 vs 18 May 2020), not the same weekday. The challenge explicitly forbids LoDs
and asks for table calculations instead; the author's own solution actually
ended up needing neither, so the interesting work is the equivalent-day logic:

- **Same day last year**: 18 May 2021 is a Tuesday; the equivalent is Tuesday
  19 May 2020. Because 2020 is a leap year and the date is after February, the
  calendar date must move forward one day (two if the leap year sits before
  February), otherwise the weekday shifts.
- **Same day last month**: if 18 May is the 3rd Tuesday of the month, the
  comparison is the 3rd Tuesday of April (20 April 2021). When the previous month
  has no 5th occurrence of that weekday the calculation must fall back to the
  4th, so the logic truncates the exact same date last month to the start of the
  week that begins on the selected weekday, then checks whether adding a week
  stays inside the previous month.

## Tableau solution chain

```text
Orders (Sample - Superstore) extract: Order Date, Sales
→ pSelectedDate (date, default #2021-05-18#)
→ pComparison (integer 1|2|3 with aliases Same Day Last Year / Last Month / Last Week)
→ Exact Date Prev Month = DATE(DATEADD('month', -1, [pSelectedDate]))
→ DoW Selected Date = DATEPART('weekday', [pSelectedDate], 'Sunday')
→ Prior DoW Prev Mth = DATETRUNC('week', [Exact Date Prev Month], <that weekday>)
→ Next DoW Prev Month = Prior DoW Prev Mth + 1 week
→ Equivalent Day Last Month = IF MONTH(pSelectedDate) = MONTH(Next) THEN Prior ELSE Next
→ Equivalent Day Last Year = leap-aware DATEADD('year', -1) plus 1 or 2 days
→ Compare Date = CASE pComparison { Last Year | Last Month | -1 week }
→ Selected Date Sales  = IF [Order Date] = [pSelectedDate] THEN [Sales] END
→ Compared Date Sales  = IF [Order Date] = [Compare Date]   THEN [Sales] END
→ % Difference = (SUM(Selected) - SUM(Compared)) / SUM(Compared)
→ Dates To Show = [Order Date] BETWEEN [Compare Date] AND [pSelectedDate]
→ BAN sheet: MIN(1) bar, fixed 0..1 axis, label = Selected Date / Selected Date
  Sales / % Difference / vs. Compared / (pComparison: Compare Date), colour = % Difference
→ Chart sheet: Sales by exact Order Date (filtered to Dates To Show) with
  Selected Date Sales / Compared Date Sales / Minus 500 on a shared second axis
  and a value label on the -500 points
→ Reset sheet: 'Reset' text plus Default Date = DATE(#2021-05-18#)
→ dashboard actions: click Chart point → set pSelectedDate; click Reset → set
  pSelectedDate to Default Date; True→False filter action suppresses the
  default selection highlight
```

## Required behavior

- `ww20-compare-date-logic`: `Compare Date` resolves to the equivalent weekday
  for each of the three comparison modes, including the leap-year and
  missing-5th-occurrence cases.
- `ww20-selected-compared-sales`: the two per-day sales measures isolate the
  selected and compared day's sales.
- `ww20-percent-difference`: the BAN shows `(selected - compared) / compared`
  with the ▲/▼ custom format.
- `ww20-ban`: the BAN bar uses `MIN(1)` on a fixed 0..1 axis, is coloured by
  `% Difference`, and labels Selected Date, Selected Date Sales, % Difference,
  the compared value and `(pComparison: Compare Date)`.
- `ww20-line-chart-dates-to-show`: the line chart plots Sales by exact Order Date
  restricted to the window between Compare Date and pSelectedDate, with a second
  axis carrying Selected Date Sales, Compared Date Sales and Minus 500.
- `ww20-parameter-actions`: a parameter action sets `pSelectedDate` from the
  clicked Order Date, the reset sheet sets it back to 18 May 2021, and a
  True→False filter action prevents the selection highlight.

## Allowed visual differences

- Fonts, padding, borders and decoration may differ unless they affect the
  result.
- The author's exact 24-swatch custom diverging palette is reproduced on the BAN
  colour legend; minor stroke widths differ.

## cwtwb baseline

Tested with the released SDK `0.27.1` (`4cd2c61c`).

- Parameters, calculated fields (including `DATETRUNC(...,'week',...)`,
  `DATEPART('weekday',...,'Sunday')`, `DATEADD`, `MONTH`, `YEAR`), `configure_chart`
  with `label_runs`/`label_extra`/`axis_fixed_range`/`color_style`, and
  `configure_layered_chart` with a `Multiple Values` pane all build natively.
- `add_dashboard_action(action_type="parameter", source_field=..., aggregation="attr")`
  emits the native `edit-parameter-action` for both the chart click and the reset
  button; `field_mappings={"True": "False"}` emits the "Don't highlight" filter
  action. No workaround is required.

No reusable capability gap was identified for this case.
