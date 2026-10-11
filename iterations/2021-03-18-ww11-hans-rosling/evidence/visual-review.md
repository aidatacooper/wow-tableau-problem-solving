# WW11 Cloud acceptance — Hans Rosling animated bubble chart

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
Replica SHA-256 `df2e083df718c6f5ca5d1e342a18236e1d9b27df639c26267b6eea5538b3d97c`
(rebuilt: see `evidence/cloud-verification.json` for the frozen hash actually
captured). SDK `4cd2c61` (0.27.1).

The author image (`outputs/cloud-author.png`) shows the target: for 2021, 185
country bubbles plotted on a **logarithmic** income axis against life
expectancy, sized by population, coloured by eight regions, with a large pale
grey "2021" behind the marks and a region bar driving a highlight action. The
replica (`outputs/cloud-replica.png`) reproduces every one of those elements.

## What was checked

- **Data**: the Cloud CSV export of the replica Scatter worksheet returns 185
  rows for 2021, and all 185 match the locked-extract oracle exactly on income,
  population, region and life expectancy (`evidence/functional-verification.json`,
  `outputs/cloud-replica-scatter.csv`).
- **Log axis**: the income axis carries `scale="log"`, which is what makes the
  shape readable; a linear axis is visibly wrong.
- **Regions**: eight region colours are present and the region bar lists the
  eight UPPER-cased region names.
- **Year**: the year card renders the selected year at 72pt pale grey.
- **Interaction contract**: a `tsc:brush` highlight action sources the Region
  sheet into the dashboard.

## Accepted visual differences

- The replica's 72pt year text sits at the sheet origin rather than centred,
  because the REST image export does not apply the desktop centring. The year is
  legible and correctly reflects the parameter.
- Region label truncation (`AFRICA SUB SA..`) matches the author's own
  truncation of the long region names.
- Fonts, exact bubble colours, axis title wording and the absent "speed control"
  (which Tableau Public omits anyway) are allowed differences.

## Not claimed

This is not a pixel match, and no browser click, hover, pager animation or
highlight execution is claimed. The native Pages shelf that drives the author's
animation is not exposed by the SDK; the replica substitutes a Year parameter and
a `Selected Year` filter, which is recorded as a `capability_gap`. The
multi-table logical-relationship path was abandoned for a normalized single
table; the failure is recorded as a separate bug finding.
