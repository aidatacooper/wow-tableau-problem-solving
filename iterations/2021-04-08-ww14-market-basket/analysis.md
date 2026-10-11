# 2021-04-08-ww14-market-basket

## Problem

Week 14 asks for a basic market-basket analysis on the Superstore dataset: on a
customer's **second order**, when they bought a chosen Sub-Category, what *else*
did they buy? Two sheets answer it — a horizontal bar chart and a treemap, both
ordered by the count of orders — and a toggle switches between them. Each
"other" Sub-Category is coloured by whether it was profitable. Order counts,
sales and profit must reflect only second orders.

## Why the obvious approach fails

- **"First order" is a data-source-filter trick, not a plain filter.** The
  article identifies a first order with `{FIXED [Customer ID]: MIN([Order
  Date])} = [Order Date]` and then keeps only `False` at the data-source level,
  so after that filter the *second* order becomes the minimum date. A worksheet
  filter alone would not shift the LoD's domain. The article also gives the
  self-contained alternative
  `{FIXED [Customer ID]: MIN(IIF([Is Customer's First Order]=False, [Order
  Date], NULL))} = [Order Date]`, which needs no extract-filter ordering; this
  replication uses that so the workbook is portable.
- **The selected Sub-Category must not appear as its own recommendation.**
  Filtering rows to orders that contain the selected Sub-Category leaves that
  Sub-Category in the data, where it would top the chart. It has to be recoded
  (`Other Items Ordered` → `'N/A'`) and excluded.
- **Only whole orders count.** Filtering on rows where the selected
  Sub-Category appears is not enough; the *other* rows of those same orders must
  survive. That is the order-level set (`{FIXED [Order ID]: SUM(...)} >= 1`),
  which the article implements as a Set and explicitly offers as this LoD.
- **A toggle needs a parameter action, not a show/hide button.** The author's
  switch is a two-axis control whose selection writes the `Toggle` parameter;
  each chart is then gated on the parameter value so exactly one has data.

## Tableau solution chain

```text
Superstore extract (Order ID, Order Date, Customer ID, Sub-Category, Sales, Profit)
→ customer's second order:
     Is Customer's First Order = {FIXED [Customer ID]: MIN([Order Date])} = [Order Date]
     Is Customer's 2nd Order   = {FIXED [Customer ID]:
                                  MIN(IIF([Is Customer's First Order]=False,
                                          [Order Date], NULL))} = [Order Date]
→ orders containing the selected Sub-Category:
     pSelected_SubCat                (string list, default Accessories)
     Customer Ordered Selected SubCat = IIF([pSelected_SubCat]=[Sub-Category],1,0)
     Orders with Selected SubCat      = {FIXED [Order ID]:
                                          SUM([Customer Ordered Selected SubCat])} >= 1
     Other Items Ordered              = IF [pSelected_SubCat]=[Sub-Category]
                                          THEN 'N/A' ELSE [Sub-Category] END
→ measures:
     Count Orders = COUNTD([Order ID])
     Profit Ratio = SUM([Profit])/SUM([Sales])
     Is Profitable? = [Profit Ratio] > 0
→ three filters on both charts: 2nd order = True, Orders with Selected SubCat = True,
     Other Items Ordered excludes 'N/A'
→ Bar:     Other Items Ordered on Rows, Count Orders on Columns,
           Colour = Is Profitable?, shelf-sort by Count Orders DESC
→ Treemap: Square marks, Size = Count Orders, Detail = Other Items Ordered,
           Colour = Is Profitable?, computed-sort by Count Orders DESC
→ Toggle:  MIN(0) and Selected Toggle on a synchronised column axis, Circle on
           the parameter axis; a parameter action writes Toggle on select
→ observable result: exactly one chart is visible, ordered by order count, with
  profitable Sub-Categories grey and unprofitable ones orange.
```

## Required behavior

- Only a customer's second order contributes; first orders are excluded by an
  LoD, not by row order.
- The charts count orders that contain the selected Sub-Category and show the
  *other* Sub-Categories on those orders; the selected Sub-Category is excluded.
- Bars and tiles are ordered by the distinct order count descending.
- Marks are coloured by whether the other Sub-Category's profit ratio is
  positive.
- Selecting on the Toggle control sets the `Toggle` parameter, and exactly one
  of the bar chart and treemap renders at a time.

## Allowed visual differences

- Fonts, padding, borders, label wrapping and the exact grey/orange shades are
  decorative.
- The author's `Data` debugging sheet is not reproduced.
- Header/footer text zones and the parameter control styling differ.

## cwtwb baseline

`cwtwb 0.27.1` (commit `4cd2c61c`) built the whole solution with public APIs
only:

- `add_parameter` for the Sub-Category list and the 0/1 Toggle;
- `add_calculated_field` for the two `FIXED` LoDs and the order-set LoD;
- `configure_chart` for the Bar (with `sort_descending`/`sort_field`) and
  `configure_layered_chart(sort_mode="computed")` for the Detail-bound treemap
  sort and Square marks;
- `configure_custom_tooltip` per sheet;
- `configure_worksheet_style` plus a datasource colour palette for the boolean
  profitability colouring, and quantitative range filters for the Toggle gates;
- `add_dashboard_action(action_type="parameter", source_field="Measure Names")`
  for the switch and `action_type="filter"` with `field_mappings={"True":
  "False"}` for the deselect behaviour;
- a nested `layout-flow` container so the toggled-off worksheet collapses to
  zero height and the visible chart fills the region.

No workaround and no reusable capability gap, so `cwtwb_result` is `pass`.
