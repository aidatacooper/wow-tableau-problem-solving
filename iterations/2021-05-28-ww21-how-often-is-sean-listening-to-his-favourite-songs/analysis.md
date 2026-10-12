# 2021-05-28-ww21-how-often-is-sean-listening-to-his-favourite-songs

## Problem

One dot per song (x = days between the first and last time the song was played,
y = total plays) with a range filter on total plays, and — when a song is
clicked — that song's dot is replaced by a stepped running-total timeline of its
plays, drawn on the same axes.

## Why the obvious approach fails

The scatter works at one row per song while the timeline needs one row per song
*and* date, so the two charts live at different levels of granularity. The
author's solution keeps them on a single dual-axis worksheet by making every
mark's value depend on whether the song is in a `Selected Song` set:

- the scatter branch (`OUT` of the set) plots `SUM([Days since first listen])`
  against `SUM([Total Plays per Song])` — one mark per song;
- the timeline branch (`IN` the set) plots `AVG([Days To Date])` against
  `RUNNING_SUM([Total Plays])`, with `[Date Played]` on Detail and Path, which
  turns the selected song's dot into a per-day cumulative step line.

The tricky part is that removing `[Date Played]` from the Total Plays marks card
would also remove the selected song's own dot, so the author adds
`Is Last? = LAST()=0` and `Last Plays to Plot = IF [Is Last?] THEN SUM([Total
Plays per Song]) END` to keep exactly one circle per song. `Last Plays to Plot`
carries the `Total Plays per Song` axis, and `Plays to Plot` rides a synchronised
second axis whose axis is hidden.

## Tableau solution chain

```text
data (SongID, Performer, Song, TimeStamp_UTC)
→ Date Played = DATE(DATEPARSE("MM/dd/yyyy HH:mm", [TimeStamp_UTC])) with the
  AM/PM fallback
→ Min Date per Song / Max Date per Song = {FIXED [SongID]: MIN/MAX([Date Played])}
→ Days since first listen = DATEDIFF('day', min, max)
→ Total Plays = COUNT(*); Total Plays per Song = {FIXED [SongID]: [Total Plays]}
→ Days To Date = DATEDIFF('day', min, [Date Played])
→ Selected Song set (empty-level, filled by an on-select set action)
→ Days to Plot  = IF ATTR([Selected Song]) THEN AVG([Days To Date]) ELSE SUM([Days since first listen]) END
→ Plays to Plot = IF ATTR([Selected Song]) THEN RUNNING_SUM([Total Plays]) ELSE SUM([Total Plays per Song]) END
   (table calc addressed by [Date Played])
→ Is Last? = LAST()=0; Last Plays to Plot = IF [Is Last?] THEN SUM([Total Plays per Song]) END
→ Chart: rows = Last Plays to Plot + Plays to Plot (folded, synchronised),
  cols = Days to Plot, Circle pane over a stepped Line pane, filter
  Total Plays per Song 50..100
→ dashboard: change-set action (single select) + highlight action on the True
  constant so marks keep constant transparency
```

## Required behavior

- `ww21-scatter-aggregates`: the per-song fields (first/last date, days between,
  total plays) are the `{FIXED [SongID]}` aggregates over the raw timestamps.
- `ww21-selected-song-set`: the `Selected Song` empty-level set exists and is
  registered with its In/Out instance.
- `ww21-plot-switch`: `Days to Plot` / `Plays to Plot` branch on
  `ATTR([Selected Song])` between the song-level and date-level measures.
- `ww21-timeline`: the second pane is a stepped Line whose Path is
  `Date Played`, and the running total is addressed by that date.
- `ww21-plays-filter`: the worksheet filters `Total Plays per Song` to 50..100.
- `ww21-interactions`: the dashboard has a single-select change-set action on
  `Selected Song` and a highlight action targeting the `True` constant.

## Allowed visual differences

- Fonts, padding, borders and decoration may differ unless they affect the
  result.
- The author keeps the right-hand axis hidden; the replica hides the axis labels
  but not the folded measure headers.

## cwtwb baseline

Tested with the released SDK `0.27.1` (`4cd2c61c`).

- `configure_layered_chart` with `axis_shelf="rows"`, `fold_axes=True` and
  `synchronized=True` builds the dual-axis worksheet; a `Multiple Values`-style
  second axis is not needed because both panes bind real measures.
- `add_set(use_all=False)` + `add_dashboard_set_action(single_select=True,
  selection_mode="assign")` emit the native `edit-group-action`.
- `add_dashboard_action(action_type="highlight", fields=["True"])` emits the
  `tsc:brush` highlight action.
- `table_calc_overrides` addresses `Plays to Plot` by `EXACTDATE(Date Played)`
  so the running total is monotone; `add_calculated_field(..., table_calc=...)`
  is available but the worksheet-level override is what Cloud honours.

Two Cloud-rendering notes were needed and are documented as workarounds rather
than capability gaps:

- A custom tooltip whose runs reference `EXACTDATE(<date field>)` renders the
  whole worksheet blank; the tooltip therefore uses the bare date fields (which
  Tableau aggregates at the month level in the tooltip text only).
- Combining `axis_style.encodings` with the folded-axis builder and a
  row `Detail` field could blank the view; the axis titles are set with
  `axis_style.per_field` alone.
