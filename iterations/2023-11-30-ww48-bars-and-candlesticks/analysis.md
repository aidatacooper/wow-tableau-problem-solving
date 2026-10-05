# Analysis: 2023 Week 48 - Can You Add Candlesticks to Bar Charts?

## Challenge Overview
Inspired by Andy Kriebel and authored by Shunta Nakajima for #WorkoutWednesday 2023 Week 48, this challenge combines paired horizontal bar charts with candlestick (Gantt) delta indicators to visualize year-over-year performance across Sub-Categories for multiple switchable measures (`Sales`, `Profit`, `Quantity`).

## Data Model & Calculations
1. **Current Year**:
   Dynamic latest year in the dataset:
   ```tableau
   {FIXED: MAX(YEAR([Order Date]))}
   ```
2. **Dynamic Measures**:
   - `Measure to Display - Curr Year`:
     ```tableau
     IF YEAR([Order Date]) = [Current Year] THEN
       CASE [Parameters].[pSelectedMeasure]
         WHEN 'Sales' THEN [Sales]
         WHEN 'Profit' THEN [Profit]
         WHEN 'Quantity' THEN [Quantity]
       END
     END
     ```
   - `Measure to Display - Comp Year`:
     ```tableau
     IF YEAR([Order Date]) = [Parameters].[pSelectedYear] THEN
       CASE [Parameters].[pSelectedMeasure]
         WHEN 'Sales' THEN [Sales]
         WHEN 'Profit' THEN [Profit]
         WHEN 'Quantity' THEN [Quantity]
       END
     END
     ```
3. **Difference & Direction**:
   - `Difference`: `SUM([Measure to Display - Curr Year]) - SUM([Measure to Display - Comp Year])`
   - `Diff is +ve`: `[Difference] >= 0` (True -> `#7fb897`, False -> `#d66252`)

## Construction & Verification Strategy
- **Construction**: 100% pure Python using `cwtwb` public `TWBEditor` starting from `TWBEditor("")`.
- **Oracle Verification**: Validates Hyper ground truth records and calculations for all 17 sub-categories across 4 calendar years.
- **Native Verification**: Checks dual-axis configuration (`Bar` + `GanttBar`), parameters, color palettes, and dashboard assembly.
