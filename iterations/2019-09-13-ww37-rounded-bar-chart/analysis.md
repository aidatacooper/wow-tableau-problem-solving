# 2019-09-13-ww37-rounded-bar-chart

## Problem

Compare each sub-category's total sales with the contribution of a selected region.

## Why the obvious approach fails

A single regional sales bar lacks the total-sales baseline required to judge
the region's contribution.

## Tableau solution chain

```text
Superstore orders → Region Param → regional sales and percentage calculations
→ comparison bar worksheet → dashboard → contribution by sub-category
```

## Required behavior

- Changing Region Param changes the highlighted contribution and percentage,
  while the all-region total remains visible.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK provides the Hyper connection, parameter, calculated fields,
multi-measure bar encodings, labels, and dashboard layout required here.
