# 2019-09-20-ww38-performance-indicators

## Problem

Compare current and prior-year sales progress and immediately identify whether performance is improving.

## Why the obvious approach fails

Raw sales totals alone do not align the comparison period or make direction of change explicit.

## Tableau solution chain

```text
Orders → aligned month and current/prior calculations → cumulative sales and percent change → KPI and line worksheets → dashboard → performance direction.
```

## Required behavior

- The dashboard shows current and prior cumulative sales plus a positive/negative percent-change state.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports the required Hyper connection, LOD/date calculations, table calculations, encodings, and dashboard layout.
