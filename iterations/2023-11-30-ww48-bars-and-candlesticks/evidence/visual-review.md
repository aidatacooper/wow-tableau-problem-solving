# Visual Review: 2023 Week 48 Bars and Candlesticks

## Overview
- **Author Viz**: Donna Coles (#WorkoutWednesday 2023 Week 48)
- **Challenge Author**: Shunta Nakajima (inspired by Andy Kriebel)
- **Dashboard Size**: 1000 x 680
- **Primary Chart**: Dual-axis bar and candlestick (Gantt) chart comparing Current Year (2023) against Comparison Year (2022) across 17 Sub-Categories, sorted descending by current year value.

## Visual Design Elements
1. **Primary Dual Axis**:
   - `Bar` mark for Current Year (`#8075ae`, muted purple) and Comparison Year (`#d3d3d3`, light grey).
   - `GanttBar` mark representing the delta (candlestick), originating at the comparison year value and extending by `Difference`.
2. **Color Palette**:
   - Delta is positive (`True`): `#7fb897` (sage green).
   - Delta is negative (`False`): `#d66252` (warm red/coral).
3. **Controls & Header**:
   - Current Year Card ("2023") styled in soft lavender.
   - Comparison Year selector tiles (`2022`, `2021`, `2020`).
   - Measure selector tiles (`Sales`, `Profit`, `Quantity`).
   - Title and footer layout match original specifications.
