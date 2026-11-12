# 2026-09-18-ww37-can-you-format-your-numbers-to-the-right-scale

## Problem

Show Segment sales with expandable Sub-Category rows while formatting each value using Tableau's undocumented `[scale]` token so thousands and millions receive a readable suffix.

## Why the obvious approach fails

A fixed thousands or millions format is wrong across hierarchy levels. The author uses `$0.0[scale]` and a parameter-driven display field so the same sheet works for collapsed and expanded segments.

## Tableau solution chain

```text
Orders extract (Segment, Sub-Category, Sales)
→ pSegment string parameter
→ Segment Display / Display calculated fields
→ bar chart with Sales labels
→ custom number format $0.0[scale]
→ parameter action on select
```

## Required behavior

- Empty `pSegment` shows one row per Segment prefixed with `+ `.
- Selecting a Segment sets `pSegment` and exposes its Sub-Categories prefixed with `- `.
- Sales labels use `$0.0[scale]`, retaining the true values while choosing k/M scale.

## Allowed visual differences

Subtotals, row hiding, typography, and spacing can differ; the hierarchy, parameter contract, and number format are the functional contract.

## cwtwb baseline

The released SDK supports the parameter, calculated fields, bar chart, parameter/highlight actions, and custom format token. Cloud/browser interaction was not executed.
