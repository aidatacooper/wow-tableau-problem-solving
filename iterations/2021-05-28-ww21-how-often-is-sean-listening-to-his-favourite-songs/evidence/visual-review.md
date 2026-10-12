# WW21 Cloud acceptance — how often is Sean listening to his favourite songs?

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Sean Miller, built by Donna Coles) asks for a scatter of one dot
per song (days between first and last listen vs total plays) with a range filter
on total plays, and — when a song is clicked — a stepped running-total timeline
of that song's plays drawn on the same axes.

## What was checked

- **Data**: the locked extract has 62,907 play rows across 15,874 songs; the
  verifier recomputes the per-song aggregates independently and confirms 89
  songs fall in the 50..100 play filter band.
- **Scatter aggregates**: `Min/Max Date per Song`, `Days since first listen`,
  `Total Plays` and `Total Plays per Song` are the `{FIXED [SongID]}` chain over
  the raw timestamps.
- **Plot switch**: `Days to Plot` / `Plays to Plot` branch on
  `ATTR([Selected Song])` between the song-level and date-level measures.
- **Timeline**: the second pane is a Circle-less stepped Line whose Path is
  `Date Played`; the running total carries an explicit table-calculation
  addressing on that date.
- **Range filter**: the worksheet filters `Total Plays per Song` to 50..100.
- **Interactions**: a single-select `edit-group-action` fills `Selected Song`,
  and a `tsc:brush` highlight action targets the `True` constant.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The author hides the right-hand axis entirely; the replica keeps the folded
  measure headers but hides the row/column field labels.
- The tooltip text uses the bare date fields (see below).

## Workarounds recorded

- A custom tooltip run that references `EXACTDATE(<date>)` blanks the Cloud
  render (1586x32). The tooltip therefore references the bare date fields; the
  tooltip's date text aggregates at the month level, which is cosmetic.
- `axis_style.encodings` combined with the folded dual-axis builder blanked the
  render in diagnostics, so only `axis_style.per_field` titles are set.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification and the native contracts.
