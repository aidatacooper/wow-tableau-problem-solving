# 2021-03-04-ww09-hide-chart-map-layers

## Problem and source identity

The dashboard should show the world's countries colored by region, then focus
on a selected country and show its urban population share as a donut. The
[official WW09 challenge](https://www.workout-wednesday.com/2021w09tab/)
was published on 2021-03-02 (WordPress post 4638). The
[Donna Coles article](https://donnacoles.home.blog/2021/03/04/can-you-hide-a-chart-in-map-layers/)
was published on 2021-03-04. These are the two business dates; the case identity
is challenge year 2021, week 9. Local date evidence records the actual downloaded
source hashes and publication timestamps.

The requirement is one worksheet in a 1000 by 800 dashboard. A parameter-driven
geographic layer changes the visible domain without replacing the source data.
The source workbook is used for analysis, data extraction and Cloud comparison.
The builder starts with `TWBEditor("")` and reads the locked extracted Hyper only.

## Data and independent arithmetic

The Hyper contains 2,691 rows: 207 unique country/year pairs for each year from
2000 through 2012. The worksheet filters the actual date field to year 2012;
the stored dates are not assumed to be January 1. The independent verifier reads
the five raw fields directly and checks every 2012 country, its region, total
population and urban ratio. The 2012 population sum is 7,014,951,860.

`Population Urban` is a share, not a population count. The complementary pie
measure is `1 - [Population Urban]`. Kosovo and St. Martin (French part) have
NULL urban shares in 2012; their complements remain NULL. There are 207 country
keys and 205 known urban ratios. Missing ratios are never replaced with zero.

| Selected country | Total population | Urban share | Non-urban share | Label |
| --- | ---: | ---: | ---: | ---: |
| China | 1,350,695,000 | 0.519 | 0.481 | 52% |
| Russia | 143,178,000 | 0.738 | 0.262 | 74% |

## Native Tableau solution

`pSelectedCountry` is a string parameter with an empty default. `All Countries`
returns the country only when the parameter is empty. `Selected Country`
returns the country only when it equals the parameter. Both calculated fields
have geographic roles. The replica's public country role serializes as
`[Country].[ISO3166_2]`, while the author's calculated roles are
`[Country].[Name]`; actual Cloud China/Russia renders and the full CSV domains
confirm the intended behavior for these inputs.

Four native map layers share one generated latitude/longitude canvas: world
polygons, selected-country polygon, a two-measure Pie, and a smaller circle
colored by region. The circle carries the centered integer-percent urban label;
Tableau automatically uses white text for China and black for Russia. Native
Measure Names and Measure Values drive the two pie wedges. Tooltips retain
country, region, population formatted to millions and urban share.

The dashboard parameter action reads `ATTR(All Countries)` from Map on select
and writes `pSelectedCountry`; clearing assigns the empty string (`s:LROOT:`).
The verifier checks source, target, event, aggregation and clearing in the
artifact. Cloud REST renders empty, China, Russia and explicit empty reset
states. No browser selection, hover or deselection was executed or claimed.

## SDK discovery and return to the case

The released baseline `e076cd03021f39a95b23646f45f7f912733be69c` reproduced a
generic capability gap with synthetic data: legacy map overlays repeated
longitude shelves and dropped per-layer multi-measure pie encodings. They did
not preserve independent nullable geographic partitions.

The SDK now supports `configure_chart(..., map_layer_mode="native")` and
per-layer geographic detail, generated geometry, Measure Values wedge sizing,
Measure Names filtering and measure-expression color maps. Existing overlay
mode remains supported. Author-free synthetic tests cover native/overlay
behavior, nullable partitions, dependencies, palettes, upsert, invalid input,
schema order and public facade/MCP/build-spec forwarding. The case uses these
general APIs without writing XML or accessing private SDK members.

The final artifact was built and independently rebuilt in isolation with the
actual non-editable Git SDK `6f220236b58dc8a5de08ce9e2d298f5c085a95ec` (0.27.1).
SDK validation records 944 passed and 25 skipped tests and successful CI.
The isolated build had no author workbook, template, prior output or copied
Cloud evidence. Its raw/native verifier passed. Build provenance binds the
official artifact and normalizes builder source newlines to LF for Windows
and other platforms; all input/artifact/image/CSV hashes remain exact bytes.

## Complete CSV coverage and its limits

Eight REST CSVs export the entire Map worksheet, two roles across four states.
The verifier binds every export and image to the uploaded workbook hash and
request state, then independently reconciles every numeric row from raw data.
It separates visible country keys from NULL-geography aggregates rather than
using an overall row count to prove the map domain.

| States | CSV rows per role | Visible country keys | Hidden aggregate rows |
| --- | ---: | --- | --- |
| default, reset | 221 | 207 All Countries, no selected country | 12 region rows and two global pie rows |
| China, Russia | 24 | one Selected Country across four layer rows, no All Countries | 18 region rows and two global pie rows |

All region/global NULL-geography sums are checked, including the exclusion of
the selected country where applicable. Both selected pie wedges are checked at
the CSV's numerical precision. Total population is exported as rounded integer
millions and urban tooltips as rounded integer percentages; CSV comparison
proves those display precisions. Exact raw population and ratio arithmetic are
proved independently through the Hyper and native formulas. The author's
default world-layer urban tooltip column is blank; it is not evidence of all
205 exact urban ratios. The replica's additional urban tooltip values are
checked against raw values, preserving the two NULLs.

The complete 207-key CSV domain alone does not prove that all 207 geographic
shapes were geocoded and drawn. The paired PNG review separately verifies the
world view, selected-country focus, donut angles and labels, and restoration
after the explicit empty REST state. Reset rendering verifies the parameter
state; the artifact verifies its clear-event wiring.

## Visual acceptance

All eight final Cloud PNGs were examined in author/replica pairs. Conditional
world/China/Russia visibility, six region colors, donut shares, centered labels
and automatic text contrast agree. The final build removes the initial
candidate's displaced donut labels and unwanted background country names.
Remaining differences are small title/subtitle padding, vertical map placement,
footer font weight, link color and the explicit CWTWB recreation credit.
The result is `acceptable_delta`, not a pixel-identical reproduction.
