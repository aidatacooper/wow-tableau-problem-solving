# Visual review — wow-2022-ww02-can-you-build-a-weekly-year-over-year-line-chart

Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`, both
captured through the Tableau Cloud REST API at 2200×1600 and hash-bound in
`evidence/cloud-verification.json` (author workbook
`3c40cd2e…d2e0af`, replica `0424c02d…a3df7b`).

Reviewer: the case author agent that produced the replica. The numeric half of
this review is mechanical (CSV diff, pixel diff) and reproducible; no separate
reviewer pass is claimed.

## Numeric agreement (151 marks, all three year groups)

The Cloud CSV export of the dashboard crosstab carries the same fields the
tooltip renders — week position, year group, `% Sales Diff +ve/-ve`,
`TOOLTIP: Label YoY%`, week ending date and sales — for the author workbook and
for the replica. Keying both exports by (plotted week, year group) gives 151
rows on each side and identical key sets:

| Check | Result |
| --- | --- |
| Rows / key sets | 151 / 151, identical |
| Weekly sales mismatches | 0 |
| Week-ending date mismatches | 0 |
| YoY% mismatches (0.15 pp tolerance = the displayed 1-dp rounding) | 0 |
| Rows with a YoY% value | 99 (47 Current + 52 Previous) |
| Rows without a YoY% value | 52 (the 2 Yrs Ago line) — identical on both sides |

Spot rows (author | replica):

| Week | Group | Sales | YoY% |
| --- | --- | --- | --- |
| 2021-01-04 | Current | $7,297 | ▲27.8% |
| 2021-01-04 | Previous | $5,710 | ▲99.7% |
| 2021-01-04 | 2 Yrs Ago | $2,859 | — |
| 2021-11-01 | Current | $70,678 | ▲126.6% |
| 2021-11-22 | Current | $52,494 | ▲28.2% |

The same values are recomputed independently from the Hyper extract by
`verify_replication.py`, which also proves the 2019-12-30 week is not split by
calendar year.

## Structural agreement

- Three weekly lines over one continuous Jan–Dec 2021 axis, one line per year
  group, in the author's colours: Current `#9cbe30`, Previous `#a0cbe8`,
  2 Yrs Ago `#bfbfbf`.
- The colour key is the worksheet title's second line ("CURRENT | PREVIOUS |
  2 YRS AGO"), not a legend — as in the author workbook.
- The y axis is `$#,##0` from $0 with no title; the x axis has no title and
  formats its ticks `dd mmm`.
- Row gridlines are off, mark labels are off, mark sizing is off with the
  author's size (0.86756908893585205).
- Dashboard is 1100 × 800 with the sheet, the three credit lines and the
  challenge link, at the author's zone positions.
- All 151 marks exist on both sides: 47 Current, 52 Previous, 52 2 Yrs Ago.

## Pixel comparison

Whole-image diff of the two 2200×1600 captures, threshold 16 levels:
97,644 pixels (2.774%) differ, confined to four bands:

| Band (y) | What | Cause |
| --- | --- | --- |
| 51–80 | worksheet title | title font (see accepted deltas) |
| 101–127 | title colour key | same |
| 208–1380 | plot area | 0.3% axis-scale difference, so lines sit up to 3 px apart |
| 1412–1434 | x-axis tick labels | month-anchored vs week-anchored ticks |
| 1544–1567 | footer link | the author's footer prints their own post URL |

Line geometry, measured as the share of each line's pixels that have a
same-colour pixel within 2 px in the other image:

| Line | author covered | replica covered |
| --- | --- | --- |
| Current | 99.46% | 99.47% |
| Previous | 99.43% | 99.46% |
| 2 Yrs Ago | 99.82% | 99.87% |

The y-axis tick label bands are pixel-identical (all eight labels at the same
rows), so the value scale matches exactly. The horizontal scale does not: the
author's leftmost mark is at x=239 and the rightmost at x=2084; the replica's
are at 242 and 2081 — the plot is 6 px (0.3%) narrower because Tableau pads a
day-grain continuous date axis slightly differently from a week-grain one.

## Accepted deltas

1. **X-axis tick anchor.** The author's continuous *week-truncated* date pill
   ticks on week starts (11 Jan, 08 Feb, 05 Apr, …); the replica's continuous
   exact-date axis ticks on month starts (01 Jan, 01 Feb, 01 Mar, …). Same 52
   positions, same `dd mmm` format, same data. Cause: cwtwb has no
   `Week-Trunc` column instance, so the case truncates the date inside the
   calculation instead (see `analysis.md`). This is the only delta with a
   functional origin.
2. **Title font.** The author pins Tableau Medium on every title run;
   `set_worksheet_rich_title` serialises bold/fontsize/fontcolor/fontalignment
   but drops `fontname`, so the title renders in Tableau's default title font.
   Text, colours, line break and centring all match.
3. **Footer link text.** The author's dashboard prints their own post URL; the
   replica prints the challenge URL from `analysis.md`. Both link out.
4. Fonts and padding elsewhere differ slightly (allowed).

Everything the challenge asks for — three years of weekly sales on one axis,
the week ending date, the period name, and a signed, colour-coded YoY% that is
absent on the oldest line — is present and numerically identical.
