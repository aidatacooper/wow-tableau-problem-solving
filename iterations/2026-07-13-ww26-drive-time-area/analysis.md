# 2026-07-13-ww26-drive-time-area

## Problem

Let’s try the Drive Time Area asks for a Tableau dashboard that exposes the stated business interaction with Superstore-derived data.

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

- **store-map** — Map plots grocery-store MAKEPOINTs and a Union Station MAKEPOINT at 38.8977,-77.0063.
- **selected-store-kpi** — Selecting stores updates # Selected Stores through the Selected Stores set action.
- **drive-time-blocker** — The missing Drive Time selection tool is recorded as a reusable SDK capability gap.

## Allowed visual differences

Fonts, spacing, borders, and decorative styling may differ while the formulas, worksheet structure, and interactions remain observable.

## cwtwb baseline

Built with cwtwb 0.29.0a2. Result: **blocked**. The map, Union Station mark and selected-store KPI are rebuilt. The 2026.2 Drive Time selection tool and DC masking layers remain to be implemented.
