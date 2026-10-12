# 2021-04-29-ww17-generation-population

## Problem

Recreate Nathan Yau's "Generation Populations with rankings by most people
alive" in a single sheet: one bar per birth year from 1919 to 2019, grouped into
seven generations, each generation pane headed by its rank, name and total
population / percent of the whole, with the generation's first year shown as a
vertical label and dashed dividers between panes.

The decision the user needs: how many people are alive today by birth year, and
how do the generations rank against each other?

## Why the obvious approach fails

1. **There is no Year field.** The locked extract has only `SEX`, `AGE` and
   `2019 Population`. The year must be derived as `2019 - [AGE]` and moved above
   the measure line so it can drive the column shelf.
2. **The generation totals are not additive per bar.** The header under each
   pane shows the *whole generation's* population, not the bar's, so the total
   must be a `{FIXED [Generation], [SEX]: SUM(...)}` LoD repeated on every row
   of the pane; a plain `SUM` would show the per-year value.
3. **Ranks and percent are view-level, not row-level.** `RANK_DENSE` and
   `TOTAL()` only produce the right header when the generation dimension is on
   the column shelf with the correct sort; a table calculation against a flat
   list gives the wrong order.
4. **The year labels are a second axis, not a header.** The author hides the
   year member headers and plots a tiny transparent circle on a second row axis
   at the generation's first year, carrying a rotated label. A naive build shows
   101 tiny column headers instead.
5. **Pane shading alternates by generation, not by row.** A `Sort Position %2`
   boolean drives two teal shades so adjacent panes differ.

## Tableau solution chain

```text
locked extract (SEX, AGE, 2019 Population)
→ Year = 2019 - [AGE] (dimension)
→ Generation = nested IF on Year (dimension, with deliberate line breaks)
→ Total Population Per Generation = {FIXED [Generation],[SEX]: SUM([2019 Population])}
→ % of Total Population = SUM(Total) / TOTAL(SUM(Total))
→ Rank = RANK_DENSE(SUM(Total Population Per Generation))
→ Total | Percent = "72.1M | 22.0%" header string
→ Min Year per Generation = {FIXED [Generation],[SEX]: MIN([Year])}
→ Point to Plot Year Label = IF Year = Min Year AND Year<>1919 THEN 4700000 END
→ Sort Position is +ve number = Sort Position %2 = 0  (pane shading)
→ one worksheet: nested columns [Min Year, Rank, Generation, Total|Percent, Year]
  with a Bar pane (population) and a tiny transparent Circle pane (year label),
  dashed column dividers, hidden member headers, SEX = 'Total'
→ observable result: seven ranked generation panes of 1919-2019 bars
```

## Required behavior

- One bar per birth year 1919-2019 for `SEX = 'Total'`, grouped into the seven
  generations with the article's exact year boundaries.
- Each pane's header shows the generation's whole-population total, its percent
  of the total, and its dense rank by population.
- Generations appear in birth-year order; the first year of each generation is
  labelled vertically; dashed dividers separate panes.
- Adjacent generation panes alternate between the two teal shades.

## Allowed visual differences

- Exact teal shades, fonts, background tone and the precise dashed divider
  styling may differ; the ranking, totals, ordering and pane structure must not.
- The author's header wrapping from deliberate carriage returns may render at a
  slightly different height.

## cwtwb baseline

The released SDK supports every primitive the solution needs: FIXED LoDs,
`RANK_DENSE`, nested column shelves, a Bar + Circle dual row axis, dashed
dividers via `table_dividers`, background via `table_formats`, hidden headers via
`header_formats`, and the rotated label via `panes_style`. No workaround and no
reusable capability gap; the case is a `pass`.
