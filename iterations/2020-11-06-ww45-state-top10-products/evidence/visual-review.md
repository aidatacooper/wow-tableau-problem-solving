# Final Cloud review: State profits and Top 10 products

Result: **acceptable_delta** for the declared Cloud REST states plus native
artifact contracts. Replica TWBX SHA-256:
`45fa3d27e106a459d7f4878e351f9a7847a80ffa904ca1d0d343aefd7664c749`.
The artifact was built using installed Git SDK
`2056efc58cec23e05a980840e29c6d01726643f7`. The coordinator records any later
compatible final SDK verification separately; these accepted outputs were not
rebuilt after capture.

All eight dashboard PNGs and eight additional standalone Top 10 Products PNGs
were inspected against their source pairs. All 24 worksheet CSVs were checked
independently against the complete locked 9,994-line extract. Images, CSVs and
both published workbooks are hash-bound in `cloud-verification.json` and
`tooltip-worksheet-images.json`. The latter binds an immutable complete parent
capture snapshot in `tooltip-parent-capture.json`, so later status annotations
do not invalidate capture provenance.

| REST state | Map members per role | Strip members per role | Product groups per role | Product body values per role |
| --- | ---: | ---: | ---: | ---: |
| Default | 49 | 9 | 52 | 156 |
| California | 1 | 1 | 4 | 12 |
| Texas | 1 | 1 | 6 | 18 |
| New York | 1 | 1 | 7 | 21 |

Every product group has Orders, Sales and Profit; every state has all three
grand totals. The verifier checks exact complete member coverage, duplicate
rejection, full exported numeric precision and totals against raw records.
Map currency CSVs use whole-dollar formatting, so their numeric tolerance is
explicitly 0.51 dollars; full underlying state profits are independently
aggregated without rounding. Orders is **COUNT(Order ID)**, matching the actual
author workbook, despite the article's COUNTD wording. Distinct orders are
also independently calculated and are not substituted for author results.

The default continental-US extent, 49 state fills and abbreviations, loss/profit
legend, nine north-to-south seaboard blocks, three-column product matrix and
totals all appear. The corrected qualified 0..1 axis restores full-width strip
blocks; omitted basemap boundary layers have been disabled. California and
New York display their isolated profitable polygons; Texas displays its
isolated loss polygon. The dynamic legend endpoints change consistently with
the source. All standalone product-state images show readable metric values
and totals, with positive/negative Profit cells retaining the source meaning.

Remaining differences are visual: the seaboard heading wraps to two lines;
title/footer spacing, font weight and URL appearance differ; standalone
product images use wider metric columns, earlier product-name truncation and
more saturated mixed-sign Profit extremes. The standalone author worksheet
also shows right-side legend cards that are absent from the replica's
standalone window. These do not hide any validated metric or alter native
independent measure domains. No pixel-identical claim is made.

**Interaction coverage is deliberately narrower than hover execution.**
Ordinary REST State filters produce the subset of global Top 10 products with
facts in that state, as observed for both workbooks. They do not execute the
compound State Abbrev/State tooltip context or demonstrate state-local Top 10
membership. Selected State filters replace the strip's original nine-member
filter; the strip therefore shows California, Texas or New York in those
states. The complete raw oracle verifies every state's independent Top 10
ranking, including states with fewer than ten products. Native inspection
verifies context-before-TopN, both source and target member columns and real
instances, recursive calculated dependencies, and the 500x350 tooltip
viewport. The extra images render the standalone worksheet, not that viewport.
No browser hover or click was executed or claimed.

Earlier failed layout and VIT-target dependency captures remain preserved in
analysis scratch, with formal gap/failure records. They are not presented as
accepted evidence. Final direct verification passes all raw, packaged-data,
native, 24 CSV and 16 image hash checks.
