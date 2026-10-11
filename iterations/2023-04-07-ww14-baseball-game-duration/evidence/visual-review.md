# Visual review — wow-2023-ww14-baseball-game-duration

Reviewer: independent AI agent (continuation of agent 0afdd9b0)
Date: 2026-10-11
Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`
(both captured via Tableau Cloud REST at 1400×1400, hash-bound in
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
- Challenge credits and the baseball-reference data footnote are present, and
  match the author's text zones byte-for-byte after reproducing the author's
  `fontname='Tableau Medium'` runs, the source hyperlink, and the 4px text-zone
  margins (those three regions now diff at 0 pixels).
- The worksheet title (bold headline + 12pt subtitle) renders on the
  worksheet itself, and the dashboard zone keeps it visible.
- The Index pill is bound as an ordinal instance, so the bars fill their
  cell width like the author's (a quantitative Index turns Columns into a
  continuous axis and renders thin strips).

## Colour agreement

The boolean palette matches the author exactly: teal `#52b7d8` for
at-or-below the 2023 pace and orange `#e16032` for slower years. The Cloud
renderer previously fell back to its default categorical blue/orange for
this case because the colour field is a table calculation. The cwtwb fix
(PR #9, `configure_chart` carrying the worksheet table-calc context onto the
datasource palette column-instance) makes the palette render, and the
verifier now asserts both the palette buckets and their table-calc context.

## Pixel comparison

A whole-image diff of the two 1400×1400 captures reports 73,748 pixels
(3.76%) differing by more than 30 levels; 96.2% of all pixels are identical,
and the entire residual is inside the plot area — the title, credits, and
source rows now diff at **0 pixels**.

The dashboard geometry matches after reproducing the author's zone margins
(root `margin=8` + a 4px margin on the Viz and text zones, a 12 dashboard px
inset): the title and the credits rows start at the same y-positions as the
author's.

## Accepted deltas

- **Reference-line placement.** The author addresses `Latest Duration` with a
  specific-dimension table calc ordered by `[Decade], [Year]`, so
  `WINDOW_MAX` resolves to the global 2023 value (158) and the "2:38 in 2023"
  line sits at the same offset (55px from the pane top) in every decade. The
  replica's table calc addresses by Year alone, so it partitions per Decade:
  the line drifts (39–61px) and evaluates to that decade's last year
  (~163–195) instead of 158. cwtwb's `table_calc_overrides` cannot express the
  author's specific-dimension addressing without also changing the bar
  ordering; the `order: [Decade, Year]` form was tested and regressed the
  render to 32.9%. Numeric agreement is unaffected — the verifier recomputes
  the classification from the extract and the bar values and labels match.
- The author's second reference line is a 150% percentage distribution band
  (`percentage-bands='true'`, `<reference-line-value percentage='150'/>`)
  used purely as row breathing space. cwtwb has no public API for percentage
  distribution bands; injecting the author's band XML was tested and moved
  the bars the wrong way (6.7%).
- Fonts and padding differ slightly (allowed).
