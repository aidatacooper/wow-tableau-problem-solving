# 2021-12-16-ww50-can-you-recreate-this-drill-down

## Problem

Lorna Brown's Week 50 challenge asks for a two-sheet, 500 x 600 dashboard that
lets a user drill from Category to Sub-Category in a bar chart while a line
chart updates to the selected scope. The stated difficulty is the reset: after
selecting Office Supplies then Art, clicking Technology directly must show
Technology, not an empty line chart left over from the previous Sub-Category.

The decision the dashboard supports is therefore a *navigation* decision, not a
new aggregate: the user should be able to move down and across the product
hierarchy without first clearing the previous selection.

## Why the obvious approach fails

A normal filter action cannot drive this dashboard. Filtering the line chart
from the bar chart removes the unselected Category bars, so the user can no
longer click another Category to move sideways. A plain parameter action also
fails on its own: if it only writes `pSelectedSubCat`, the previous
Sub-Category survives a new Category click and the line filter evaluates to no
rows.

The author's first published workbook carries an extra `pLevel` parameter and
`Max Level` / `DD Level` calculations. Her blog post says that version worked on
Desktop but failed on Tableau Public, and that the final solution did not need
the level fields. The required behaviour can be expressed with two parameters,
one display calculation and one Boolean filter.

## Tableau solution chain

```text
Superstore extract (Order Date, Category, Sub-Category, Sales)
→ parameters pSelectedCategory, pSelectedSubCat (string, default "")
→ Sub Cat Display: show Sub-Category only under the selected Category
→ FILTER: all rows when nothing is selected; Category rows when only the
  Category is selected; Category + Sub-Category rows when both are selected
→ Bar Chart: Category / Sub Cat Display on Rows, SUM(Sales) on Columns,
  Category on Colour, Sales labels, Sub Cat Display sorted descending
→ Line: continuous month-truncated Order Date on Columns, SUM(Sales) on Rows,
  Colour:Line = pSelectedCategory, FILTER = True, min/max labels
→ two on-select parameter actions on the Bar Chart, both clearing to ""
→ 500 x 600 dashboard with both sheets and the challenge title/footer
```

The reset is a property of the bar hierarchy. While `pSelectedCategory` is
Furniture, every other Category's `Sub Cat Display` evaluates to an empty
string. Clicking Technology therefore fires the Sub Cat action with a blank
value in the same gesture that fires the Category action. The two parameter
values become `("Technology", "")`, and the line chart shows the whole
Technology Category.

## Required behavior

- Default state: all three Categories are visible in the bar chart and the line
  chart shows all monthly sales.
- Click Furniture: the bar chart expands Furniture's Sub-Categories and the
  line chart shows Furniture only.
- Click Bookcases: the line chart narrows to Furniture / Bookcases.
- Click Technology directly: the Sub-Category is cleared and the line chart
  shows Technology, not a blank scope.
- Clearing the selection resets both parameters to the empty string.

## Author workbook versus the final route

The published author workbook still carries `pLevel`, `Max Level` and `DD Level`.
Its bar chart expands only after the separate "Set Level" parameter action runs,
so setting `pSelectedCategory` through the Cloud REST parameter API changes the
line chart but leaves the category bars collapsed. The blog's rebuilt solution
dropped those fields. The replica follows that final route: `Sub Cat Display`
depends directly on `pSelectedCategory`, so the bar chart expands as soon as the
Category parameter is written. This is a deliberate correctness choice, not a
visual delta.

## Allowed visual differences

- The author sorts both Category and Sub Cat Display descending. The released
  `cwtwb` chart API exposes one shelf sort; the replica keeps the more important
  inner sort (Sub Cat Display descending by Sales) and leaves Category in its
  natural order. This changes bar order, not any value or interaction.
- Category colours, fonts, padding and exact footer alignment differ. The
  author's category palette is not stored explicitly in the workbook.
- The author's line chart uses the same £ axis format; the replica matches the
  visible min/max labels and monthly shape.

## cwtwb baseline

Built end to end with released `cwtwb` 0.29.0a2 and only public APIs:
`set_hyper_connection`, `add_parameter`, `add_calculated_field`,
`configure_chart`, `configure_worksheet_style`, `add_dashboard`,
`add_dashboard_action` and `save`. The SDK already emits the schema-gated
`ParameterAction` / `ParameterActionClearSelection` manifest entries and the
native `edit-parameter-action` payload, including `clear-option`
`assign-fixed-value` with `s:LROOT:`.

No SDK workaround is required. The only limitation observed is that
`configure_chart` accepts a single descending shelf sort, so the two-level
Category + Sub-Category sort cannot be reproduced through the public API in one
call. That is a visual ordering delta, not a functional gap.
