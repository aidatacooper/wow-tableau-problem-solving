# 2019-10-14-ww41-customers-costing-us

## Problem

Identify customers whose discounting and sales mix produce weak or negative profitability.

## Why the obvious approach fails

Profit totals alone hide whether a customer has weak margin because of discounting or low-value sales.

## Tableau solution chain

```text
Orders → customer profitability calculations → scatter and detail table → diagnostic dashboard.
```

## Required behavior

- A user can see profit ratio, weighted discount, lost sales, and total customer sales together for each customer.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports the locked Hyper connection, FIXED and aggregate calculations, scatter marks, text tables, and dashboard layout.
