# 2019-10-19-ww42-comparative-line-dynamic-inputs

## Problem

Compare sales in a selected period against the immediately preceding equal-length period.

## Why the obvious approach fails

Calendar-aligned lines alone cannot compare arbitrary ranges selected by a user.

## Tableau solution chain

```text
Orders → date and range parameters → current/prior boundaries and indexed sales → line comparison → dashboard.
```

## Required behavior

- Date and time-range changes recalculate both equal-length periods.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports date/integer parameters, date arithmetic, calculated fields, multi-measure line charts, and dashboard layout.
