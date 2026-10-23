# 2021-08-31-ww34-how-many-consecutive-starts

## Problem

Luke Stanke's Week 34 challenge asks a question every NFL fan argues about:
**how many games in a row has one quarterback started for each franchise?**
The answer is a 32-row strip chart — one row per team, one bar per regular
season game from 2006 week 1 to 2020 week 17 — where each bar's height is the
length of the running consecutive-start streak at that game. The row is labelled
with the streak the team carried into its last game, so a reader can compare
"who is on a long run right now" (BLT 5, CAR 5, CIN 2) against "who has the
longest single run in the period" (LAC, 224 games).

The decision the chart supports is a roster-stability judgement: a long current
streak means one healthy starter, a short one means the team is churning.

## Why the obvious approach fails

- **Counting games is not counting streaks.** `COUNT([player_id])` per team is
  240 for everybody. The answer needs a *running* comparison against the
  previous game, which is a table calculation, not an aggregate.
- **A `{FIXED}` LOD cannot see row order.** The streak depends on the ordering
  of games within a team, so the calculation has to be addressed by the view
  (`LOOKUP`/`PREVIOUS_VALUE`), with the partition set to Team.
- **The extract is not the regular season.** `qb_starters` also carries weeks
  28-32 (334 rows, the postseason/off-season artefacts in the source CSV). Left
  unfiltered they would extend the strip past week 17 and corrupt the streaks.
- **A date axis is wrong here.** The author deliberately plots a dense game
  index (`INDEX()`), not Season/Week, so that bye weeks do not leave gaps and
  every team's 240 games line up in one continuous axis.
- **One measure on the Rows shelf is not enough.** The row header needs the
  discrete `Current Streak` value *and* the continuous `Consecutive Streak`
  axis at the same time; Tableau expresses that as a nested Rows shelf.

## Tableau solution chain

```text
qb_starters (season, week, offense_franchise_id, player_id, player)
⨝ NFL_Teams (franchise_id, team)          logical relationship, many:1
→ filter Week 1..17                        regular season only
→ Prev Player ID        = LOOKUP(MIN([player_id]),-1)
→ Match Prev Player ID  = MIN([player_id]) = [Prev Player ID]
→ Consecutive Streak    = IF NOT match OR NULL THEN 1 ELSE 1+PREVIOUS_VALUE(-1)
→ Current Streak        = WINDOW_MAX(IF LAST()=0 THEN [Consecutive Streak] END)
→ INDEX()               dense game index, restarts per team
→ Viz: Bar chart, INDEX on Columns (continuous), Team / Current Streak /
       Consecutive Streak on Rows, Season / Week / Player Id on Detail,
       Player on Tooltip, custom mark size 1 axis unit aligned right
→ dashboard 800x1800: the Viz sheet plus the four footer credits
```

Addressing for all four table calculations is **Season → Week → Player Id**,
partitioned by **Team** (Team is the outermost Rows pill, so Tableau's default
partition already restarts the run at each team).

## Required behavior

- The strip has exactly 32 team rows of 240 bars each, on a continuous index
  axis from 1 to 240.
- Every bar's height equals the running count of consecutive games started by
  the same player id, restarting at 1 whenever the player id changes or the team
  changes (see the oracle in `verify_replication.py`, which recomputes all 7 680
  regular-season rows independently of the workbook).
- `Current Streak` shows, on every bar of a team's row, the streak value from
  that team's last game.
- Both worksheets filter to weeks 1..17 and nothing else.
- The Viz bars are one flat colour (`#4f15c2`), 1 axis unit wide, right-aligned,
  with no stroke, no labels, and the Consecutive Streak axis hidden.

## Allowed visual differences

- Fonts, padding, borders and decoration may differ unless they affect the
  result. The replica keeps the author's Times New Roman workbook font, the
  `#f5f5f5` pane background, the 56/60 px row-header widths and the 52 px row
  height.
- The author's `Template` crosstab sheet (a scratch view she used to check the
  calculation chain) is not reproduced; `Data` is rebuilt instead as the tabular
  sheet that shows the same five calculated columns.

## cwtwb baseline

`cwtwb` 0.29.0a1 (commit `23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`) covers
everything this case needs through public APIs:

- `set_hyper_connection(tables=..., relationships=...)` for the two-table
  logical relationship the author used (`offense_franchise_id = franchise_id`).
- `add_calculated_field(table_calc=...)` for `LOOKUP`, `PREVIOUS_VALUE`,
  `WINDOW_MAX` and `INDEX`.
- `configure_chart(table_calc_overrides=...)` to write the Season → Week →
  Player Id addressing plus the nested-calculation dependency metadata.
- `configure_layered_chart` for the nested Rows shelf (discrete Team and
  Current Streak headers around the continuous Consecutive Streak measure),
  `mark_sizing` for the 1-axis-unit right-aligned bars, and
  `configure_worksheet_style(axis_style=..., header_formats=...)` for the hidden
  streak axis, the index axis title and the row-header widths.

Two documented case workarounds, no SDK change requested:

1. **Integer dimensions are inspected as measures.** `set_hyper_connection`
   registers `season` and `week` as measures (only names containing
   `id`/`code`/`zip` stay dimensions), and a bare `Week` field is bound as
   `MONTH(Week)` by the date-name heuristic. The workbook therefore re-exposes
   `Season`, `Week`, `Player Id` (and a continuous `Week Number` for the
   in-range filter) as explicit discrete calculated fields, which is also how
   the article presents them ("change this field to be discrete").
2. **Mixed discrete/continuous Rows shelf.** `configure_chart` nests measures
   with `*` and dimensions with `/`, producing `Team * (Current * Consecutive)`;
   the author's shelf nests Team around a product of the two streak measures.
   `configure_layered_chart` with `axis_shelf="columns"` emits the correct
   `Team / (Current * Consecutive)` form.

Baseline detail: `evidence/sdk-baseline.json`.
