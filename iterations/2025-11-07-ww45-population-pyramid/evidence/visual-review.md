# Visual review — wow-2025-ww45-population-pyramid

Reviewer: independent AI agent (continuation of agent 13d48385)
Date: 2026-10-10
Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`
(both captured via Tableau Cloud REST, hash-bound in
`evidence/cloud-verification.json`).

## Per-age numeric agreement

The replica's mark labels were read from `outputs/cloud-replica.png` and
compared with the author's export. Every age group agrees on Males,
Females (negative), and Headcount Gap sign/magnitude:

| Age | Total | Other | Males | Females | Gap  | Sign |
| --- | ----- | ----- | ----- | ------- | ---- | ---- |
| 20  | 196   | 11    | 86    | -99     | -13  | men  |
| 25  | 224   | 14    | 101   | -109    | -8   | men  |
| 30  | 364   | 10    | 163   | -191    | -28  | men  |
| 35  | 387   | 20    | 177   | -190    | -13  | men  |
| 40  | 354   | 10    | 167   | -177    | -10  | men  |
| 45  | 241   | 5     | 124   | -112    | +12  | women|
| 50  | 131   | 5     | 62    | -64     | -2   | men  |
| 55  | 67    | 3     | 33    | -31     | +2   | women|
| 60  | 22    | 1     | 7     | -14     | -7   | men  |
| 65  | 7     | 1     | 5     | -1      | +4   | women|

These values also match the independent Hyper aggregate computed by
`verify_replication.py` (10 age bins, 4 women-led bands, 6 men-led).

## Structural agreement

- Two-axis mirrored pyramid (Males + Females) with constant-zero reflines
  on the shared axis and on the independent Headcount Gap axis.
- 9 visible age bands (20–65) on the rows shelf, with `:ok` ordinal
  Total Headcount and Other Gender nested under Age Group — matching the
  author's `(/ (/ ...))` row nesting.
- Cols shelf is `(Females + (Males + Gap))` mirroring the author's fold.
- Three bars per band on the pyramid panes and one bar per band on the
  Gap pane — four panes total (anchor + 1 + 2 + 4), matching the
  author's pane id layout.
- Mark labels render on every bar with the bold cull=false treatment
  that forces labels on the narrow bars.
- Challenge title and credits text are present on the dashboard.

## Accepted deltas

- **Bar colors**: the Cloud-rendered bars fall back to Tableau's default
  categorical palette (blue/orange) instead of the author's Men/Women
  pair (purple `#8175aa` / green `#6fb798`). We inject a
  ``<encoding attr="color" field="[:Measure Names]">`` block in the
  worksheet and datasource style-rules with the author palette, but
  Cloud Server's renderer does not honor it for the dual-axis panes; it
  does honor it for the third (Gap) pane. Documented in `case.yaml`
  `capability_gaps`; the visual evidence captures this as the single
  remaining structural deviation.
- The author's `Males (copy)` / `Females (copy)` rename is reproduced
  via `set_measure_name_aliases`; this affects the visible pill name
  but not the column-instance reference Cloud uses for the encoding
  bucket, which is why the encoding does not match.
- The Headcount Gap bar color toggles per cell via the boolean flag in
  the author; in the replica, the Gap pane uses a single color (the
  default Tableau orange). Cloud Server's boolean color encoding is
  honored only when the encoding is on the pane's `color` mark, not via
  the global Measure Names palette.
- Fonts, padding, and title font colour match the author; the title
  font colour for the "Men" / "Women" tokens uses Tableau defaults
  rather than the author's purple/green tokens.
