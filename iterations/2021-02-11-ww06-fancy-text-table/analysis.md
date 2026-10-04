# Monthly sales progress report

Article date: 2021-02-11. Official challenge date: 2021-02-10, from WordPress
post 4470 rather than an assumed Tuesday. Identity: 2021 WW06.

The business question is how every month in the latest available year compares
with the previous year, which actual trading dates have the highest/lowest
daily sales, and which six months have the highest current-year sales. The
author's single worksheet uses Measure Names on Columns, Order Month on Rows,
and Measure Values on Text and Color with separate domains. The eight measures
are CY SALES, LY SALES, CY vs LY, △, % DIFF, BEST DAY, WORST DAY and RANK.

The packaged Hyper is already restricted to 2019 and 2020: 5,899 records, two
columns (Order Date and Sales), date range 2019-01-02 through 2020-12-30. This
locked input is extracted once. The builder reads this Hyper and starts from
`TWBEditor("")`; it never reads the source workbook or its XML. Source XML is
used solely for analysis, source Cloud publication and data extraction.

Current Year is derived from the maximum input Order Date, not hardcoded.
Monthly sales aggregate the relevant year's rows. Daily sales aggregate all
current-year orders on each observed date, and per-month extrema select the
latest tied date, matching the author's MAX date selection. Missing dates do
not become zero-sales candidates. BEST DAY and WORST DAY remain numeric
measures: Tableau INT(date) plus two corresponds to the date serial formatted
with `dd mmm yyyy`. RANK uses descending competition rank and SIZE()/2; the
nested table calculations use the author's Columns addressing.

The published source differs from some article examples: the monetary delta is
black and has no positive plus prefix, the percentage difference is red/green,
and the rank labels are uppercase TOP/BOTTOM. The replica follows the actual
published source. All eight independent continuous palettes have two steps.
The dashboard is 1200 by 800, with the source's normalized table and footer
geometry. Tooltip suppression is a native artifact contract. There are no
source parameters, actions or dynamic controls to execute.

The released noneditable Git SDK fe9 baseline supports the complete case:
native measure tables, independent measure color domains, custom numeric
formats, nested table-calculation contexts, rich titles and floating layouts.
No case-specific or private API is introduced.

Acceptance requires independently computing all 96 table cells from raw locked
Hyper records, checking every author and replica REST CSV cell, binding both
PNG and CSV captures to the published source and frozen replica hashes, and
directly comparing the images. CSV coverage is the full monthly report, not a
button or a partial worksheet. REST screenshots do not prove browser events;
no browser interaction is claimed. The automatically generated phone layout
is outside the desktop acceptance scope.
