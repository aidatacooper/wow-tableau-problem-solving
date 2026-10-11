# Visual review — wow-2022-ww32-dumbbell-chart

Reviewer: independent AI agent (continuation of agent 13d48385)
Date: 2026-10-10
Evidence: `outputs/cloud-author.png` vs `outputs/cloud-replica.png`
(both captured via Tableau Cloud REST at 2000×1600, hash-bound in
`evidence/cloud-verification.json`).

## Per-age numeric agreement

The replica's mark labels were read from `outputs/cloud-replica.png` and
compared with the author's export (`outputs/cloud-author.png`). Every age
group agrees on both years and on the labelled difference:

| Age | 2015 | 2019 | Difference | >20 pts |
| --- | ----- | ----- | ---------- | ------- |
| 8   | 11%   | 19%   | ▲8%        | no      |
| 9   | 15%   | 26%   | ▲11%       | no      |
| 10  | 19%   | 36%   | ▲17%       | no      |
| 11  | 32%   | 53%   | ▲21%       | yes     |
| 12  | 41%   | 69%   | ▲28%       | yes     |
| 13  | 50%   | 72%   | ▲22%       | yes     |
| 14  | 59%   | 81%   | ▲22%       | yes     |
| 15  | 71%   | 83%   | ▲12%       | no      |
| 16  | 73%   | 89%   | ▲16%       | no      |
| 17  | 74%   | 88%   | ▲14%       | no      |
| 18  | 77%   | 91%   | ▲14%       | no      |

These values also match the independent Hyper aggregate computed by
`verify_replication.py` (11 ages, 4 above the 20-point threshold: 11–14).

## Structural agreement

- Each age shows two dots joined by a vertical connector — one shared
  folded/synchronized Measure Values scale, Circle pane + Line pane.
- Connectors for ages 11–14 are coloured as the >20-point class; the rest
  use the default class. Same split as the author.
- Circle colours (2015 `#98d3a2` / 2019 `#5e50a4`) and connector colours
  (true `#cd3e4c` / false `#a2a2a2`) match the author's palettes exactly.
- The ▲ difference label sits directly below the lower (2015) circle, the
  same anchor the author renders. The anchor is deterministic: the builder
  pins `internal_name` on Ownership 2015/2019 so the Measure Names full
  reference for 2015 is always the lexicographic minimum, which is where
  `mark-labels-mode=range` + `range-min` anchors the label. With cwtwb's
  default per-build UUID names the anchor flipped between the top and
  bottom circle across rebuilds.
- The "Dummy" header row is hidden; the Age header 8–18 stays visible.
- Challenge title and credits text are present on the dashboard.

## Pixel comparison

A whole-image diff of the two 2000×1600 captures reports 1189 pixels
(0.037%) differing by more than 16 levels, confined to the bbox
x 871–1179, y 199–222 — the coloured runs of the subtitle's second line.
Every other pixel, including all mark labels, connectors, headers and
credits, is identical.

## Accepted deltas

- The subtitle's coloured runs ("2015", "2019", "ages 11-14") render at
  the regular weight; the author pins them to the Tableau Bold face with
  `fontname` on the run. cwtwb's `set_worksheet_rich_title` serialises
  bold/fontsize/fontcolor/fontalignment but drops `fontname`
  (configure_custom_tooltip accepts it), and the case's public-SDK-only
  boundary rules out patching the attribute afterwards. Known cwtwb
  capability gap; everything else matches.
- Fonts and padding differ slightly (allowed).
