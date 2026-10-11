# 2021-04-23-ww16-quick-lods

## Problem

Week 16 (Tableau 2021.1's Quick LoDs) asks for one sheet: a dual-axis chart
showing each Sub-Category's Sales against the **Sub-Category Average Sales by
Category**, with the percent difference labelled on the bars and the bars
coloured by whether they beat that average.

## Why the obvious approach fails

- **`AVG([Sales])` is the wrong average.** The required benchmark is the mean of
  the *Sub-Category totals* inside each Category, not the mean of raw order
  rows. A Category with many small Sub-Categories would be dragged down by the
  row count. The Quick LoD chain is `{FIXED [Sub-Category]: SUM([Sales])}` then
  `{FIXED [Category]: AVG([Sales (Sub-Category)])}`.
- **The second Quick LoD starts as SUM.** Dragging the first LoD onto Category
  creates `{FIXED [Category]: SUM(...)}`; the aggregation has to be edited to
  `AVG` or the benchmark is the Category total.
- **A single measure cannot show the benchmark behind every bar.** The Category
  average is a constant per Category, so it needs its own axis and a full-height
  GanttBar mark behind the Sales bars, with the two axes synchronised.
- **The percent difference needs a custom format.** Tableau's `▲0%;▼0%` format
  supplies the up/down triangle from the sign, which a plain percentage cannot.

## Tableau solution chain

```text
Superstore extract (Category, Sub-Category, Sales)
→ Quick LoD 1: Sales (Sub-Category) = { FIXED [Sub-Category]: SUM([Sales]) }
→ Quick LoD 2: Sales (Sub-Category) (Category)
                 = { FIXED [Category]: AVG([Sales (Sub-Category)]) }
→ comparison:
     Difference = (SUM([Sales]) - SUM([Sales (Sub-Category) (Category)]))
                  / SUM([Sales (Sub-Category) (Category)])     (*▲0%;▼0%)
     Colour     = [Difference] > 0
     Above | Below = IF [Difference] > 0 THEN 'Above' ELSE 'Below' END
→ one dual-axis sheet:
     Rows:  Category / Sub-Category (sorted by Sales descending)
     Cols:  SUM(Sales) + SUM(Sales (Sub-Category) (Category))  (synchronised)
     pane 1  Bar      colour = Colour, label = Difference
     pane 2  GanttBar flat grey, full-height size, no labels
→ tooltip: Category | Sub-Category, Sales, Difference, Above|Below,
           the Category average
→ observable result: teal bars where the Sub-Category beats its Category
  average, grey bars where it does not, each labelled with the signed percent
  difference.
```

## Required behavior

- The benchmark is the mean of Sub-Category totals within each Category
  (6 Sub-Categories for Furniture and Technology, 13 for Office Supplies).
- Each Sub-Category shows its sales and its percent difference against that
  benchmark, with the sign and triangle.
- Bars are coloured teal when above the average and grey when below.
- The benchmark renders as a full-height grey backdrop behind the bars, with
  both axes synchronised.
- The tooltip names whether the Sub-Category is Above or Below.

## Allowed visual differences

- Fonts, padding, the exact teal/grey shades and the footer text are
  decorative.
- The Category header band styling is approximated.

## cwtwb baseline

`cwtwb 0.27.1` (commit `4cd2c61c`) built the whole solution with public APIs
only:

- `add_calculated_field` for both `FIXED` LoDs (including the nested
  `AVG`), the difference, the boolean colour and the Above|Below text, with
  `default_format="*▲0%;▼0%"` and the currency format;
- `configure_dual_axis(dual_axis_shelf="cols")` with a Bar pane and a GanttBar
  pane, `synchronized=True`, `size_value_2`, `mark_color_2`;
- `set_datasource_color_palette` for the boolean palette;
- `configure_worksheet_style(panes_style=...)` to give the Gantt pane its own
  hidden-label mark styling;
- `configure_custom_tooltip` per pane.

No workaround and no reusable capability gap, so `cwtwb_result` is `pass`.
