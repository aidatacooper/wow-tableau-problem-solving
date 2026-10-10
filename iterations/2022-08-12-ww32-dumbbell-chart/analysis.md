# 2022-08-12-ww32-dumbbell-chart

## Problem

How did smartphone ownership among US teens and tweens change between 2015 and
2019? A single bar chart of two years forces the reader to compare heights by
eye. The question is really about the *change* per age, so the two years should
be shown as two dots joined by a line — a dumbbell — with the gap made explicit.

## Why the obvious approach fails

A grouped bar chart per age puts the two years side by side but never draws the
change: the reader has to subtract mentally, and a 20-point gap looks the same
as a 2-point gap at a glance. Plotting a single "difference" bar loses the two
underlying levels, so the reader cannot see whether a large gap is 11%→19% or
77%→91%.

The dumbbell needs both dots *and* the connecting line, and the line has to be
coloured by whether the change is large. That means one worksheet carrying two
marks with different encodings on two synchronized measure axes.

## Tableau solution chain

```text
data domain (one row per Age × Year: Ownership)
→ calculations
    Ownership 2015  = IF [Year]=2015 THEN [Ownership] END
    Ownership 2019  = IF [Year]=2019 THEN [Ownership] END
    Difference      = SUM([Ownership 2019]) - SUM([Ownership 2015])
    Difference>0.2  = [Difference] > 0.2
→ worksheet
    Age on Columns (discrete), two Measure Values axes on Rows
    pane 1: Circle, Measure Names on Colour, values labelled on the dots
    pane 2: Line,  Difference>0.2 on Colour, Difference on Label,
            Measure Names on Path
→ dashboard
    the worksheet plus the challenge title and credits
→ observable result
    each age shows two dots joined by a line; lines where ownership grew by
    more than 20 points are coloured differently, and the gap is labelled
```

The two measure axes are synchronized so both dots sit on the same scale; the
line pane shares that scale, which is what makes the connector horizontal and
correctly positioned.

## Required behavior

- `Ownership 2015` / `Ownership 2019` isolate the two survey years.
- `Difference` is `Ownership 2019 - Ownership 2015` and is formatted as a
  percentage.
- `Difference>0.2` is a boolean that is true exactly when the change exceeds
  20 percentage points.
- The worksheet carries a Circle pane and a Line pane over the same Age axis.
- `Age` is discrete (8–18), so the eleven age groups appear as separate columns.

## Allowed visual differences

- Fonts, padding, and the exact dot/line colours may differ.
- The author's tooltip wording is reproduced; the mark-label styling may differ.

## cwtwb baseline

Built with the released cwtwb pinned in `requirements.txt` using only public
APIs: `set_hyper_connection`, `add_calculated_field`, `add_worksheet`,
`configure_layered_chart` (two panes, synchronized axes, `mark_sizing_off`),
`configure_worksheet_style`, `configure_custom_tooltip`, `add_dashboard`.
No reusable capability gap was found.
