# 2025-11-07-ww45-population-pyramid

## Problem

How is the workforce distributed across age bands, and where does the gender
balance tip? The reader should see one horizontal bar per 5-year age band with
women extending left and men extending right from a shared zero line, plus a
per-band headcount-gap column showing which gender dominates that band.

## Why the obvious approach fails

Two side-by-side bar charts (one per gender) force the reader to compare bar
lengths across two separate charts. Mirroring the genders around a common zero
axis makes the imbalance within each band instantly visible, and an explicit
gap column quantifies it — including which gender is the minority in that band.

## Tableau solution chain

```text
data domain (one row per person: Age, Gender)
→ calculations
    Age Group        = 5-year bin of Age
    Total Headcount  = {FIXED [Age Group]: COUNT(rows)}
    Other Gender     = {FIXED [Age Group]: SUM(IIF([Gender] not Male/Female,1,0))}
    Males            = IIF([Gender]='Male',1,0)
    Females          = IIF([Gender]='Female',-1,0)   (negative for mirroring)
    Headcount Gap    = SUM([Males]) + SUM([Females])
    Colour - Gap     = [Headcount Gap] < 0
→ worksheet (dual axis, synchronized)
    Rows:    Age Group (discrete), Total Headcount (discrete),
             Other Gender (discrete) — nested row headers give spacing
    Columns: Females + Males (dual axis, synchronized) + Headcount Gap
    Marks:   Bar on all cards; Measure Names colours the two gender axes;
             Headcount Gap pane coloured by Colour - Headcount Gap
    Labels:  all bars labelled bold, middle-centre
    Reference lines: constant 0 solid black line on the Females axis and the
             Headcount Gap axis
    Top axis hidden; gridlines and column dividers removed
→ dashboard 1300×700 with credits and the #RWFD data note
→ observable result
    each 5-year band shows mirrored male/female bars plus a gap bar whose
    colour names the majority gender; every bar is labelled with its headcount
```

## Required behavior

- The 5-year bin groups ages 22–65 into bands 20, 25, …, 65.
- `Females` is negative, so female bars extend left of zero.
- `Headcount Gap` = males − females per band; negative means more women.
- `Colour - Headcount Gap` is True exactly when the gap is negative
  (women outnumber men in that band).
- Both axes carry a constant-0 solid reference line.
- All three bar panes label their marks; row headers stay visible.

## Allowed visual differences

- Bar colours may use default palettes rather than the author's exact hues.
- Fonts, row heights, and label placement may differ slightly.
- The numeric bin may be produced by a calculation rather than a native bin.

## cwtwb baseline

Built with the released cwtwb pinned in `requirements.txt` using only public
APIs: `set_hyper_connection`, `add_calculated_field` (FIXED LODs, the signed
gender splits, the gap and its colour flag), `add_worksheet`,
`configure_dual_axis` (Females/Males synchronized bars), `configure_layered_chart`
is not needed — the third axis (Headcount Gap) is added through the layered
declaration of three column panes, `add_reference_line` for both constant-0
lines, `configure_worksheet_style`, `configure_custom_tooltip`, and
`add_dashboard`.

cwtwb has no native numeric-bin primitive (only `add_group` categorical bins),
so the 5-year bin is expressed as the public calculated field
`INT([Age] / 5) * 5` with an explicit ordinal declaration — no reusable SDK
gap, since Tableau's own bin is equally a derived field.
