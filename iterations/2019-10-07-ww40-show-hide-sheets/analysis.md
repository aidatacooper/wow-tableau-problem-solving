# 2019-10-07-ww40-show-hide-sheets

## Problem

Switch the visual presentation of monthly sales without changing the measure or date grain.

## Why the obvious approach fails

Duplicating data logic for each presentation would make comparable views drift over time.

## Tableau solution chain

```text
Orders → display-type parameter → shared monthly sales → area/bar/line and previews → dashboard.
```

## Required behavior

- The workbook contains all three equivalent presentations and the packaged display-type parameter.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports parameters, multiple worksheets, chart marks, Hyper input, and dashboard layout.
