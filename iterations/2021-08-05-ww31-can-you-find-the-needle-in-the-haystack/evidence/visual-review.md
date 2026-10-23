# Visual review — WW31 needle in the haystack

Compared the Tableau Cloud renders of the author workbook and the cwtwb
replica (`outputs/cloud-author.png` vs `outputs/cloud-replica.png`), both
captured through the same REST path at `imageresolution=High`.

## What matches

| Element | Author | Replica |
| --- | --- | --- |
| Product rows, order, count | 13 products, Sales DESC | 13 products, Sales DESC, identical |
| Title line 1 | "Can you Figure Out Which Unprofitable, High Sales Products to Focus On?" | same text |
| Title line 2 legend | `Higher` grey / `Lower` orange / "Average Number of Customers" grey | same colours and wording |
| Row text block | Product Name on line 1, `Sub-Category \| Category` grey on line 2, left aligned | same two-line block, same grey sub-line |
| Bar colours | orange for lower-than-average, grey for higher | identical per-product assignment (13/13 verified from REST CSV) |
| Bar labels | `$23K`, `$18K`, … right of each bar | identical values |
| Sales bar start column | constant left offset from the invisible `MIN(1)` bar | same |
| Footer | CHALLENGE BY : CANDRA MCRAE / #WOW2021 \| WEEK 31 / RECREATED BY : DONNA COLES + URL | same three cells and URL, third cell reads "RECREATED WITH cwtwb" |
| Dashboard size | 800×650 fixed | 800×650 fixed |

## Accepted deltas (visual_status = acceptable_delta)

1. **No horizontal separator rules between rows.** The author draws a thin
   light-grey row divider (table-div, `stroke-size` 1, `solid`); the replica
   keeps table dividers off for a clean background. Row rhythm is preserved by
   the 51px row height.
2. **Title typography.** The author's title uses Tableau's own semibold face at
   12pt; the replica uses the default family with `bold=true` at 12pt. Text,
   size and colour match; the typeface differs by one weight step.
3. **Bar geometry.** The author's bars are slightly wider with a small gap
   above/below; the replica's bars fill the row band edge-to-edge because
   `mark-sizing` is `marks-scaling-off` on both panes. Both keep the same
   proportional lengths.
4. **Footer attribution.** The third footer cell credits cwtwb rather than the
   original author, per the repository convention for replicas.
5. **Titles of the hidden sheets.** The replica has no separate `Data` scratch
   sheet (that sheet exists only so the author could eyeball the components);
   every one of its measures is verified numerically by `verify_replication.py`
   against the locked extract instead.

## Numeric agreement (stronger than pixels)

The REST CSV export of the author `Data` sheet and the replica `Chart` sheet
agree on all 13 products with zero differences:

- membership: 13/13 identical product names (Top 50 = `In`, Unprofitable = `In`)
- `Higher than Avg Customer Count`: 13/13 identical booleans
- `Customer Count Per Product`: 13/13 identical integers
- `SUM(Sales)`: identical at the `$K` display precision

No product is present in one view and absent from the other.
