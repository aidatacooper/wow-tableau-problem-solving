# 2021-03-18-ww11-hans-rosling

## Problem

Recreate Hans Rosling's iconic "200 Countries, 200 Years, 4 Minutes" animated
bubble chart: for each year from 1800 to 2021, plot every country as a bubble
where the x axis is income per person (log scale), the y axis is life
expectancy, the bubble size is population and the bubble colour is the country's
region. The viewer pages through the years, watching the world move up and to
the right, and can highlight one region to isolate it against the rest.

The decision the user needs: at a given year, how do income, life expectancy and
population relate across regions, and how did each region move over time?

## Why the obvious approach fails

Three things break a naive build:

1. **The source is three separate wide matrices, not one fact table.** Life
   expectancy, population and income each arrive as `country × year` matrices in
   their own Hyper table. A single extract does not contain the three measures on
   one row, so a scatter of income vs life expectancy cannot read them from one
   table. The author pivoted each file and related the three extracts on
   country **and** year. Rebuilding from one physical table would either drop a
   measure or mis-align the years.
2. **The Income axis must be logarithmic.** Income spans 245 → 179,000, so a
   linear axis crushes the poorest countries into the left edge and hides the
   story. The author explicitly sets a log scale on the Income axis. A plain
   continuous axis renders the wrong shape.
3. **The year must be readable inside the chart and drive the marks.** The
   author overlays a large grey "Year" sheet under a transparent Scatter sheet,
   and the Scatter is paged by Year. Without the pages shelf and the transparent
   scatter background the year is either invisible or the scatter hides it.

## Tableau solution chain

```text
4 locked Hyper tables (Life Expectancy, Population, Income, Regions)
→ logical relationships on country (+ year for the three measure tables)
→ Region = UPPER(REPLACE([eight_regions],'_',' '))
→ filters: Year ≤ 2021 (context/all), exclude null Eight Regions
→ Scatter: pages=Year, cols=Income (dimension, continuous, log axis),
           rows=Life Expectancy (dimension, continuous),
           detail=Country, size=SUM(Population), colour=Region,
           mark=Circle, transparent worksheet background
→ Year: text table of Year, 72pt pale grey, centred, sits under the Scatter
→ Region: row of region labels, drives a highlight action onto Scatter
→ dashboard: Year sheet behind a floating transparent Scatter, Region bar on top
→ observable result: one bubble per country per year, sized by population,
   coloured by region, log income axis, animated by the year pager
```

## Required behavior

- One mark per country for the selected year, positioned by that country's
  Income (x, log scale) and Life Expectancy (y) for that year.
- Bubble size is the country's population for that year; colour is the region.
- Years beyond 2021 and countries with no region are excluded.
- Paging the Year control changes which year's facts are plotted.
- Selecting a region label highlights that region's bubbles on the scatter.

## Allowed visual differences

- Fonts, exact bubble colours, padding, borders and the "speed control" that
  Tableau Public omits may differ.
- The author keeps the Year sheet as a separate worksheet under a transparent
  Scatter; the replica reproduces the layering and the 72pt pale-grey year text
  but need not match pixel positions.

## cwtwb baseline

Record what the released SDK supports, any local workaround, and any reusable
capability gap.
