# 2019-09-04-ww35-drill-up-down-parameter-actions

## Problem

Show annual sales at category level, then reveal the selected category's
sub-categories through a level parameter.

## Why the obvious approach fails

Putting Category and Sub-Category on the view together permanently removes
the compact category-level comparison needed before drilling.

## Tableau solution chain

```text
Superstore orders
→ Select Category and Level Param
→ FIXED annual category and sub-category sales
→ Level, Display, and Display Sales calculations
→ bar worksheet and dashboard
→ category totals or selected-category detail
```

## Required behavior

- Level Param 1 shows category totals; Level Param 2 expands the selected
  category to sub-categories while retaining annual sales.

## Allowed visual differences

- Fonts, padding, borders, and decoration may differ unless they affect the
  result.

## cwtwb baseline

The released SDK supports Hyper connections, parameters, FIXED calculations,
bar encodings, and dashboard layout. The click-triggered parameter action is
represented by the exposed parameters; no reusable SDK gap was required.
