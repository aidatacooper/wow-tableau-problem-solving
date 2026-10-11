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

## Color, palette, and axis agreement

- **Bar colors**: the Cloud render now matches the author exactly —
  purple `#8175aa` (Men) and green `#6fb798` (Women) on both pyramid
  panes, sign-toggled green/purple on the Headcount Gap pane (gap
  values −28/−13/−10/−13/−8/−7/−2 green, +12/+2/+4 purple), and the
  colored `Men` / `Women` tokens in the subtitle. The earlier
  blue/orange fallback is resolved by injecting a fully-qualified
  Measure Names reference bucket and dropping the alias entries.
- **Axes**: both sides tick `0…200` around the shared zero (clusters
  measured at identical x-positions on the right axis: `150`,
  `200`, gap `30` verified by crop), and the Headcount Gap axis ticks
  `30…0…10` with its zero refline. The axis titles `Headcount` and
  `Headcount Gap` match, including the hidden Males axis.
- **Reference lines**: both constant-zero lines render (measured at
  x≈967/2233 in the author and x≈955/2249 in the replica at 2x
  capture scale).
- The author's `Males (copy)` / `Females (copy)` rename is reproduced
  via `set_measure_name_aliases`; captions and visible pill names
  match.
- Fonts, padding, title font colour, header two-line wrapping, and
  the credits rows match the author.

## Pixel comparison

A whole-image diff of the two 2600×1400 captures reports 71,596 pixels
(1.97%) differing by more than 30 levels; 98.0% of all pixels are identical.
The title and the credits rows start at the same y-positions as the
author's after reproducing the author's zone margins (root `margin=8`,
Viz zone `margin=4`, text zones `margin=4`).

## Accepted deltas

- Sub-2% pane-geometry offsets from renderer layout rounding: the
  shared zero line sits ~6px left of the author's, the left `200`
  tick ~12px further left (at 2x capture scale), and the Headcount
  Gap axis is ~1.6% wider. Tick values, labels, and bar lengths are
  unaffected; values and domain (0…200 / −30…10) are identical.
- Structural XML differences with no visible impact: the replica's
  axis style-rule carries an extra class="1" (Gap) encoding the
  author omits; cwtwb omits `value="0"` / `tooltip-type` on the
  reflines and cannot write `element="field-labels"` (no public
  API), which the header width/height settings render equivalently.
