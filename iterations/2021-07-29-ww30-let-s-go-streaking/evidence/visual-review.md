# WW30 Cloud acceptance — Let's go streaking! (PENDING)

Status: **not evaluated.** No accepted Cloud capture exists for the current
artifact. Do not read this file as a visual acceptance.

## What the local checks do cover

`verify_replication.py` recomputes the entire table-calculation chain in Python
from the locked Hyper extract (9,994 order lines → 782 month × Sub-Category
rows) and asserts it against the workbook's own XML contracts:

| Sub-Category | longest streak | peak month(s) | peak sales |
| --- | --- | --- | --- |
| Appliances | 5 | 2017-11 | $6,611.97 |
| Bookcases | 5 | 2019-06 | $5,309.07 |
| Phones | 5 | 2019-09 | $15,318.84 |
| Art | 4 | 2019-06 | $1,019.10 |
| Envelopes | 4 | 2019-11 | $518.63 |
| Supplies | 4 | 2019-01 | $4,314.41 |
| Tables | 4 | 2017-09, 2019-11 | tied |
| Binders | 2 | 7 tied months | tied |
| Storage | 2 | 7 tied months | tied |

These match the article's own screenshots (`image-58.png`, `image-72.png`):
Appliances 5, Bookcases 5, Phones 5, Art 4 in that order.

## What the first Cloud capture showed (rejected)

Capture `2026-10-23T15:21:11Z`, SDK `23b1df0` (0.29.0a1):

- The author workbook published and exported a 314 KB CSV.
- **The replica rendered empty.** All three replica sheets (`Chart`, `Legend`,
  and even the plain `Data` text sheet) showed only their titles; the replica
  CSV was 0 bytes. Dashboard text zones rendered normally, so the failure was in
  the worksheets, not the dashboard container.

Three structural causes were identified and fixed locally afterwards:

1. **Custom-tooltip run pointed at `EXACTDATE(<date field>)`.** This is the
   documented batch-17 hazard (ww20/ww28): a tooltip run on that expression makes
   Tableau Cloud render the whole worksheet empty (1586×32 / blank pane). Runs now
   reference the bare date field.
2. **The month axis used `EXACTDATE(Order Date Month)`**, i.e. an exact-date
   instance over a calculated date. Tableau cannot bind that instance; the
   author's own workbook uses the native `Month-Trunc` instance of the raw date
   (`[tmn:Order Date:qk]`). The builder now uses `MONTHTRUNC(Order Date)`.
3. **`Sort` was quantitative and `Legend` was a measure.** A quantitative leading
   pill emits an extra axis instead of nesting under `Sub-Category`, and the
   legend needs a discrete ordinal instance for its header plus a quantitative
   instance for the colour ramp. Both are now built as the author does.

The row shelf now matches the author's own nesting exactly:
`((Sort / (Sub-Category / Longest Streak)) * (Sales + Peak Sales))`.

## Still required before this case can be accepted

- Re-run the Cloud capture against the current artifact and confirm the
  dashboard renders (non-blank, non-degenerate image) and that the replica `Data`
  CSV matches the oracle row by row.
- Run the Desktop gate (`build_and_check.py`) and confirm `LOADED`.
