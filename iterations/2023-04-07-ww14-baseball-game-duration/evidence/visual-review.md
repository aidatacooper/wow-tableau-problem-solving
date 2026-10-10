# Visual review — wow-2023-ww14-baseball-game-duration

Reviewer: independent AI agent (continuation of agent 13d48385)
Date: 2026-10-10
Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`
(both captured via Tableau Cloud REST, hash-bound in
`evidence/cloud-verification.json`).

## Numeric agreement

The replica's mark labels were read from `outputs/cloud-replica.png` and
compared with the author's render. Every rendered year (1960–2023) agrees on
both the h:nn duration and the pace classification:

- 2023 = 2:38 (158 minutes), matching the independent Hyper aggregate in
  `verify_replication.py`.
- Blue (at-or-below the 2023 pace): 1960–1984 — every bar labelled with its
  year and duration, identical values to the author.
- Orange (slower than 2023): 1985–2022 plus 2023 itself, identical values.
- The class boundary falls at 1984/1985 in both renders.

## Structural agreement

- Decade rows 1960s–2020s, one bar per year, ordered by the Year-addressed
  INDEX() table calc.
- A "2:38 in 2023" custom-labelled reference line spans every decade pane in
  both renders.
- Duration axis, Index header, and field labels are hidden; tooltips off.
- Challenge credits and the baseball-reference data footnote are present.

## Accepted deltas

- Bar bodies are narrower than the author's (the author's bars nearly touch;
  ours keep a small gap). The labelled values and colour classes are
  unaffected.
- Label placement sits just below the bar top rather than inside the bar.
- The colour legend is hidden in our replica (the author's is off-canvas);
  both renders rely on the same two-class palette.
- Fonts and padding differ slightly.
