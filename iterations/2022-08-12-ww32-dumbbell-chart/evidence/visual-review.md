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
- The difference label renders next to the lower dot with the ▲ format.
- The "Dummy" header row is hidden; the Age header 8–18 stays visible.
- Challenge title and credits text are present on the dashboard.

## Accepted deltas

- Dot/line colours use the default palettes rather than the author's exact
  greens/purples (allowed: exact colours may differ).
- Dot labels show on both dots; the author's label placement is marginally
  different (allowed: mark-label styling may differ).
- Fonts and padding differ slightly (allowed).
