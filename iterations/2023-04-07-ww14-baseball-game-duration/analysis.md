# 2023-04-07-ww14-baseball-game-duration

## Problem

How long did Major League Baseball games take, year by year, and how does each
year compare with the 2023 pace? The reader should scan one bar per year,
grouped into decade rows, and immediately see whether that year ran longer or
shorter than 2023 — the year the pitch clock was introduced and games suddenly
sped up.

## Why the obvious approach fails

A plain year-by-year bar chart buries the comparison: the reader has to find
2023 at the far right and visually subtract each bar against it. The challenge
instead encodes the comparison as *colour* (each year at-or-below vs above the
2023 duration) and pins the 2023 value as a labelled reference line, so the
"speed-up" story is visible without reading any axis.

## Tableau solution chain

```text
data domain (one row per Year: Time/9I game duration)
→ calculations
    Duration (mins)  = DATEPART('hour',[Time/9I]) * 60 + DATEPART('minute',[Time/9I])
    Decade           = STR(FLOOR([Year]/10) * 10) + 's'
    Index            = INDEX()          (compute by Year)
    Latest Duration  = WINDOW_MAX(IF LAST()=0 THEN SUM([Duration (mins)]) END)
    Duration > Latest= SUM([Duration (mins)]) >= [Latest Duration]
→ worksheet (Viz)
    Columns: Index (table calc, compute by Year; header hidden)
    Rows:    Decade (discrete) * Duration (mins)
    Detail:  Year (discrete), the measure window so the bar level is Year
    Colour:  Duration > Latest (True = at-or-faster than 2023)
    Label:   Year above ATTR(Time/9I) formatted h:nn, bottom-centred
    Reference line (per pane): average of Latest Duration,
             custom label "2:38 in 2023", line only, tooltip off
    Second reference band (150% distribution) purely for row breathing space
→ worksheet (Data)
    text table: Year / Decade / Index / Duration > Latest rows,
    Measure Names columns with Duration (mins) + Latest Duration
→ dashboard 700×700 with credits and data-source footnote
→ observable result
    each decade shows one bar per year coloured by faster/slower than 2023,
    each bar labelled with the year and its h:nn duration, and a "2:38 in
    2023" reference line spans every decade pane
```

## Required behavior

- `Duration (mins)` converts the `Time/9I` datetime to total minutes.
- `Decade` buckets years into "1950s"… "2020s" strings.
- `Latest Duration` is a window calculation equal to the 2023 duration
  (158 minutes) across every row.
- `Duration > Latest` is True exactly when the year's duration is at or below
  the 2023 value (games that were *not* slower than 2023).
- The Year filter keeps 1960 onward, matching the author's rendering window.
- The Viz worksheet carries the "2:38 in 2023" reference line and a hidden
  Index header; tooltips are disabled.

## Allowed visual differences

- Bar colours may use the default boolean palette rather than the author's
  exact orange/blue assignment.
- Fonts, padding, and the exact label typography may differ.
- The hidden Data sheet exists for parity but is not visually judged.

## cwtwb baseline

Built with the released cwtwb pinned in `requirements.txt` using only public
APIs: `set_hyper_connection`, `add_calculated_field` (including
`table_calc="Rows"` metadata on `Duration > Latest`), `add_worksheet`,
`configure_chart` (bar chart with the Index table calc on Columns via
`table_calc_overrides`), `add_reference_line` +
`configure_reference_line_style` (custom label, hidden line style is NOT
used — the line is shown), `configure_worksheet_style`, and `add_dashboard`.
The 150%-distribution spacer band is reproduced with `add_reference_band`
using `Latest Duration` as the field endpoint.
