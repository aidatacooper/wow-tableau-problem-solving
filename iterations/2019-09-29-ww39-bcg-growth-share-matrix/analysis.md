# 2019-09-29-ww39-bcg-growth-share-matrix

## Problem

Classify sub-categories by sales growth and market share for a selected historical window.

## Why the obvious approach fails

A sales ranking cannot distinguish high-growth opportunities from mature high-share products.

## Tableau solution chain

```text
Orders → year-window parameter → current/prior sales, growth, share, quadrant → scatter and bar worksheets → matrix.
```

## Required behavior

- Changing No of Years recalculates each sub-category's growth/share quadrant.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports Hyper, parameters, LOD and table calculations, scatter encodings, and dashboard layout.
