# 2019-11-01-ww44-sales-calendar-top3

## Problem

Find daily sales patterns for one year and emphasize the three strongest sales months.

## Why the obvious approach fails

A conventional monthly chart loses weekday and week-of-year calendar context.

## Tableau solution chain

```text
Orders → year and highlight parameters → calendar coordinates and monthly sales rank → layered calendar → dashboard.
```

## Required behavior

- The selected year's dates render by week and weekday, with optional Top-3 monthly highlighting.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports Hyper input, parameters, FIXED and ranking calculations, square/text marks, and dashboard layout.
