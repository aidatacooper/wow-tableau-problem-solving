# 2021-04-15-ww15-website-analytics

## Problem

Week 15 is a dashboard-design and formatting challenge on a Google Analytics
export. It asks for four metrics, each as a BAN (big number) beside a weekly
trend line with a reference line:

| BAN | trend | reference line |
| --- | --- | --- |
| Total Sessions | weekly sessions | weekly average |
| Average Session Duration | weekly duration | overall aggregate, `mm:ss` |
| Bounce Rate | weekly rate | overall aggregate, `%1dp` |
| Average Time on Page | weekly duration | overall aggregate, `mm:ss` |

The data runs 29 Dec 2019 – 12 Apr 2021 but the answer must only include rows up
to 10 Apr 2021. Two of the metrics are durations that must render as minutes and
seconds.

## Why the obvious approach fails

- **A quick filter is not enough for the aggregates.** The overall reference
  lines are `{FIXED : [measure]}` aggregates. If the 10 Apr cutoff is a plain
  worksheet quick filter, the aggregate still sees 11 and 12 April. The article
  makes the Date filter workbook-level (data-source scoped) so the LoD's domain
  is already restricted.
- **Seconds do not format as `mm:ss`.** Tableau's `nn:ss` custom format treats
  its input as a fraction of a day, so `(SUM([Session Duration]) /
  SUM([Sessions]))/86400` is required; the raw seconds value renders nonsense.
  The article notes `mm:ss` (rather than `nn:ss`) does not give the right values.
- **The week start matters.** With a Monday week origin the weekly buckets shift
  and the numbers stop matching; the datasource week origin must be Sunday.
- **A week-of-year axis collapses the two years.** Plotting `WEEK(Date)` folds
  2020 and 2021 into 53 buckets; the author plots the continuous week-start
  date instead.
- **The average-line shortcut gives the wrong duration.** Dragging Average Line
  from the Analytics pane does not reproduce the `{FIXED : ...}` value, so the
  article builds explicit aggregate fields and references them.

## Tableau solution chain

```text
Google Analytics extract (Date, Bounces, Exits, Pageviews, Session Duration,
                          Sessions, Time on Page)
→ workbook-level Date filter: Date <= 2021-04-10 (data-source scope)
→ datasource week origin: Sunday
→ measures:
     Avg Session Duration = (SUM([Session Duration]) / SUM([Sessions]))/86400   (*nn:ss)
     Bounce Rate          = SUM([Bounces])/SUM([Sessions])                      (p0.0%)
     Avg Time on Page     = (SUM([Time on Page])/(SUM([Pageviews]) - SUM([Exits])))/86400
                                                                                (*nn:ss)
     Overall Session Duration = {FIXED : [Avg Session Duration]}                (*nn:ss)
     Overall Bounce Rate      = {FIXED : [Bounce Rate]}                         (p0.0%)
     Overall Time on Page     = {FIXED : [Avg Time on Page]}                    (*nn:ss)
→ BAN sheets: single Text mark per metric, rich label (value over title)
→ trend sheets: week-start date on Columns, measure on Rows, Line mark,
     labels on most-recent mark, reference line (average for sessions, the
     aggregate field otherwise) formatted dotted black
→ dashboard: vertical container of title / yellow spacer / four horizontal
     rows (coloured spacer + BAN + trend) / footer
→ observable result: 155,210 sessions, 03:53 average duration, 44.3% bounce
     rate, 02:19 average time on page, each with a matching reference line.
```

## Required behavior

- Four metrics are shown as a BAN and a weekly trend line each.
- The duration metrics render as `mm:ss`; the bounce rate as a percentage with
  one decimal.
- Each trend line draws a reference line: the weekly average for sessions and
  the overall aggregate for the other three.
- The aggregate matches the BAN exactly.
- Only rows up to 2021-04-10 contribute, enforced at the workbook level.
- Weeks start on Sunday, and the x axis is a continuous date so both years stay
  distinct.

## Allowed visual differences

- Fonts, padding, exact spacer widths and the footer text are decorative.
- The author's exact dashboard-pixel layout is approximated with flow
  containers.
- Label placement on the trend lines may differ slightly.

## cwtwb baseline

`cwtwb 0.27.1` (commit `4cd2c61c`) built the solution with public APIs only:

- `set_date_options(start_of_week="sunday")`;
- `add_calculated_field` with `default_format="*nn:ss"` / `"p0.0%"`;
- `add_shared_filter` for the workbook-level date scope, then an in-range
  quantitative bound on the continuous Date instance;
- `configure_chart` Text BANs with `label_runs`, and Line trends;
- `add_reference_line` with `formula="average"`/`"overall"` plus
  `configure_reference_line_style` for the dotted black line and its number
  format;
- nested vertical/horizontal flow containers with coloured `empty` spacer zones.

One implementation note, not a reusable gap: the author's x axis is Tableau's
`Week-Trunc` continuous derivation (`[twk:Date:qk]`), which the cwtwb field
registry does not name. A `DATETRUNC('week', [Date])` calculated field exposed
through `EXACTDATE(...)` produces the same continuous weekly date axis, so the
case uses that. No workaround and no capability gap, so `cwtwb_result` is
`pass`.
