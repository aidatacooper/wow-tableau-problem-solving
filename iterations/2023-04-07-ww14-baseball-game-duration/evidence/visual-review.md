# Visual review — wow-2023-ww14-baseball-game-duration

Reviewer: independent AI agent (continuation of agent 0afdd9b0)
Date: 2026-10-11
Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`
(both captured via Tableau Cloud REST at 1400×1400, hash-bound in
`evidence/cloud-verification.json`).

## Result

The two renders are **pixel-identical**: a whole-image diff reports
**0 pixels (0.000%)** differing by more than 30 levels, and 100.00% of all
pixels are exactly equal.

## Numeric agreement

Every rendered year (1960–2023) agrees on both the h:nn duration and the pace
classification:

- 2023 = 2:38 (158 minutes), matching the independent Hyper aggregate in
  `verify_replication.py`.
- Blue (at-or-below the 2023 pace): 1960–1984.
- Orange (slower than 2023): 1985–2022 plus 2023 itself.
- The class boundary falls at 1984/1985 in both renders.

## Structural agreement

- Decade rows 1960s–2020s, one bar per year, ordered by the Year-addressed
  INDEX() table calc.
- The "2:38 in 2023" reference line sits at the same offset in every decade
  pane. The author addresses `Latest Duration` with a specific-dimension
  table calc ordered by `[Decade], [Year]`, so `WINDOW_MAX` sees the whole
  table and resolves to the global 2023 value (158); the builder reproduces
  that addressing.
- The author's second reference line is a 150% percentage distribution band
  used purely for per-pane breathing room. It is transparent, but it shapes
  each pane's axis range, which is what the author's row spacing depends on.
  It is reproduced with cwtwb's `add_percentage_band`.
- The table has no column dividers (`table-div` cols off), matching the
  author's pane.
- The Index pill is bound as an ordinal instance, so the bars fill their cell
  width like the author's.
- Challenge credits and the baseball-reference source row match the author's
  text zones exactly, including the `Tableau Medium` fontname, the source
  hyperlink, and the 4px text-zone margins.

## Colour agreement

The boolean palette matches the author exactly: teal `#52b7d8` for
at-or-below the 2023 pace and orange `#e16032` for slower years, bound with
the same table-calc context as the worksheet colour instance.

## Verification notes

The percentage band must not carry `tooltip-type`. Tableau Desktop rejects a
workbook whose reference line sets it, failing with load error `d2e8da72`;
`add_percentage_band` deliberately omits it. The verifier asserts both the
band's presence and the absence of `tooltip-type`.
