# 2026-07-18-ww28-pareto-chart-coloured-backgrounds

## Problem

Can you build a Pareto chart with coloured backgrounds? asks for a Tableau dashboard that exposes the stated business interaction with Superstore-derived data.

## Why the obvious approach fails

The challenge depends on Tableau table calculations, spatial marks, sets, or parameter actions. A static chart can look plausible while losing the cumulative order, selection state, or comparison semantics that drive the result.

## Tableau solution chain

```text
extracted Hyper input
→ calculated fields / parameters / set
→ worksheets
→ dashboard actions
→ observable acceptance scenarios
```

## Reproduction notes

The Donna Coles article and author workbook were inspected during analysis. The builder reads only the extracted Hyper file under `inputs/`; it does not open or import the author TWBX.

## Required behavior

- **pareto-running-percentages** — Viz contains cumulative customer and sales percentages computed with RUNNING_SUM/TOTAL.
- **pareto-guides** — Viz includes 0.2 and 0.8 reference guides on both axes.
- **pareto-workbook-structure** — Data and Viz worksheets plus the challenge dashboard round-trip through cwtwb.

## Allowed visual differences

Fonts, spacing, borders, and decorative styling may differ while the formulas, worksheet structure, and interactions remain observable.

## cwtwb baseline

Built with cwtwb 0.29.0a2. Result: **pass**. The cwtwb build reproduces the two running percentages, area chart, fixed 0.2/0.8 guides and dashboard. Five coloured background bands and the author's explicit Sales descending sort still need a richer reference-band/sort configuration.
