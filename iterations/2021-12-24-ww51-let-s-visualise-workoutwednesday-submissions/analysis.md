# 2021 Week 51 — Let's visualise #WorkoutWednesday submissions

## Problem

The tracker contains one row per public submission. The dashboard must let a
viewer read submission volume by calendar day, compare the selected day's
submissions by whether they were made for that same challenge week, and see the
challenge week represented by each submission. A Tableau-only software filter
keeps non-Tableau submissions out of every view.

## Why the obvious approach fails

Using the raw timestamp as a mark creates one mark per submission and makes the
day-level heatmap impossible to read. Leaving the bars unfiltered also makes a
click on a heatmap cell look successful while the breakdown still reports the
whole tracker. The replica therefore derives the week number, weekday, year and
challenge label from the extract, applies the Tableau software filter to every
worksheet, and routes a heatmap selection into both bars.

## Tableau solution chain

```text
Timestamp + Challenge Week/Year + Software
→ Week Submitted / Weekday Submitted / Challenge Submitted
→ Submissions + Percentile of Submissions + Same Week Submission
→ Heatmap + Submission Type Bar + Challenges Bar
→ heatmap selection filter action
→ day-level heatmap and two matching breakdown bars
```

## Required behavior

- The heatmap contains one square per Tableau submission day, with calendar
  year on rows, weekday on rows, week number on columns, and the percentile
  calculation driving the colour scale.
- The heatmap tooltip reports the selected day's submission count and the bars
  are empty until a heatmap cell is selected.
- A selected day filters both bars to that day. The first bar separates
  “Same Week Submission” from “Other Submission”; the second ranks the
  `Challenge Year`/`Challenge Week` label for the selected day.
- Clearing the selection restores the empty breakdown state.

The independent raw-data oracle covers 8,627 rows in the packaged Hyper and
6,963 rows where `Software = Tableau`. It is the source for the default
submission count and the day-level filter contract.

## Allowed visual differences

Fonts, padding, borders, and decoration may differ when they do not change the
day bucket, filter result, bar categories, or displayed counts.

## cwtwb baseline

The workbook is authored with cwtwb 0.29.0a2 public chart, style, dashboard and
native-JSON conversion APIs. The released SDK has no direct setter for an
empty action-filter state on target worksheets, so the builder round-trips its
own generated workbook through `convert_workbook` and materializes the
empty-level filter for the two bars. It also has no calculated-field member
alias API, so the replica emits the two required submission-type labels with a
string calculation. The builder never opens or reads the author workbook.
