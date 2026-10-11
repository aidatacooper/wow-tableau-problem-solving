# Visual review — WW15 website analytics

## Scope

`outputs/cloud-author.png` and `outputs/cloud-replica.png` are the author's
published dashboard and the replica dashboard in the same default state.

## Result: acceptable_delta

The business answer is identical. Both show the title, the thin yellow rule, the
four metric rows (coloured left bar, BAN, weekly trend with a dotted black
reference line) and the footer, with matching values:

| BAN | author | replica |
| --- | --- | --- |
| Total Sessions | 155,210 | 155,210 |
| Avg Session Duration | 03:53 | 03:53 |
| Bounce Rate | 44.3% | 44.3% |
| Avg Time on Page | 02:19 | 02:19 |

The reference-line labels also match: `AVG: 2,317` for sessions and
`OVERALL: 03:53`, `OVERALL: 44.3%`, `OVERALL: 02:19` for the other three. The
Cloud CSV export of the replica Sessions BAN returns `155,210`, equal to the
author's export.

The weekly trend shapes match: the sessions spike in week 16 of 2021, the
duration settles around 4 minutes, the bounce rate around 44%, and page time
around 2:20.

## Allowed differences

- The author's x axis labels are month abbreviations with a two-digit year
  (`Jan 12, 20`); the replica shows the same format. Minor tick spacing differs.
- The reference-line label sits at the left edge in both; the exact offset
  differs by a few pixels.
- The author's BAN font sizes and row heights are slightly different.
- The footer text and dashboard padding differ.
