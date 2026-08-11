# 2019-09-09-ww36-custom-axis-tracker

## Problem

Track monthly sales while retaining quarterly context. Hovering any month on a
custom axis must draw intersecting reference lines on the line chart, then
remove both tracked lines as soon as the pointer leaves the axis.

## Why the obvious approach fails

A standard month axis does not distinguish the selected point or provide the
intentional quarterly date labels.

## Tableau solution chain

```text
Superstore orders → month/date-label calculations + empty selected-date set
→ line, custom-axis, and data worksheets → dashboard hover Set Action
→ selected date → intersecting date and Sales reference lines
```

## Required behavior

- The line chart retains a maximum Sales reference line.
- Hovering a mark on Custom Axis fills `Selected Date Set`; the Line Chart
  shows a vertical date reference line and horizontal Sales reference line for
  that month.
- Leaving Custom Axis clears the set, so the two tracked reference lines
  disappear.
- Custom Axis labels quarter starts and the final available month, while its
  remaining marks stay teal.
- Custom Axis hides its continuous date axis, uses `m-yyyy` labels in 8pt
  `#898989`, centers labels over 60-pixel cells, and renders teal `#499894`
  circles at the source mark size; labeled months use white circles.
- The Custom Axis tooltip shows the month in bold 9pt, then `Sales:` and the
  aggregated value in `#666666`, with the value bolded.
- Line Chart uses the original `#499894` line and point markers, an 8pt Sales
  axis, and the same four-run tooltip as Custom Axis.
- All three reference lines are dotted `#499894`; the vertical hover line is
  two pixels wide, and reference labels use bold Tableau Medium styling.
- Worksheet titles are hidden in both dashboard zones.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports the required Hyper connection, date parameter,
calculated fields, reference line, worksheets, and dashboard layout.
