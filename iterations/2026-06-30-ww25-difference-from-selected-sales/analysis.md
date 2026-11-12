# 2026-06-30-ww25-difference-from-selected-sales

## Problem

Can you show the difference from selected Sales? asks for a Tableau dashboard that exposes the stated business interaction with Superstore-derived data.

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

- **difference-formula** — Difference equals selected-sales subtraction, or Sales when comparison is cleared.
- **parameter-actions** — Selecting either worksheet updates pSelectedSubCat and pSelectedSales and clears to the documented defaults.
- **selector-and-bar** — Selector and Bar worksheets plus dashboard round-trip through cwtwb.

## Allowed visual differences

Fonts, spacing, borders, and decorative styling may differ while the formulas, worksheet structure, and interactions remain observable.

## cwtwb baseline

Built with cwtwb 0.29.0a2. Result: **pass**. The parameter-driven Difference formula and two-way parameter actions are rebuilt. The author's dual-axis selector shape layer and tooltip text polish remain.
