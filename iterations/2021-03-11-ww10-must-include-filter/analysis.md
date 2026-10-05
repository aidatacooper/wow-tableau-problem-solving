# 2021-03-11-ww10-must-include-filter

## Problem

A user wants to find orders that contain a chosen product, and then narrow those
orders down to the ones that *also* contain a second required product. This is
the "market basket" / "commonly purchased with" question, and it must work at a
higher grain than the underlying data: Superstore has line-item rows, but the
result is reported per order.

The dashboard must let the user pick the first product, pick an additional
product that the order must also include, then show:

- a bar chart of the surviving orders (Order ID) with their **complete**
  order-level Sales and Quantity totals;
- a hover tooltip that lists the line items of the hovered order;
- BANs for the number of qualifying orders, their share of all orders, and the
  average order amount and quantity.

## Why the obvious approach fails

Putting the product set on the Filter shelf (or as a normal categorical filter)
filters the data to the **line items** that match the chosen product. That is
wrong in two ways:

1. The order-level totals collapse to the selected product's line only, so the
   Sales/Quantity shown for an order understate the real order value.
2. The second stage becomes impossible. Once the first filter has removed all
   the other product lines, there is no data left to test whether the order also
   contains the second product.

The article walks through this failure explicitly: after filtering to the first
product the row count per customer looks right but the Sales/Quantity values
differ from the published solution, because "we have actually filtered the data
just to the lines containing the selected product".

The fix is to keep the product selection as an *order-level membership test*
rather than a row filter, and to order the two stages so the second set can only
see the products that still exist inside the already-filtered orders.

## Tableau solution chain

```text
Superstore order line items (Order ID, Customer Name, Product Name, Sales, Quantity)
→ set 1st Products        (empty-level set over PRODUCT, driven by a set control)
→ set 2nd Product         (empty-level set over PRODUCT, driven by a set control)
→ Order has 1st Products = {FIXED [Order ID]: MAX([1st Products])}
→ Order has 2nd Product  = {FIXED [Order ID]: MAX([2nd Product])}
→ filter Order has 1st Products = True  AND  Add to Context
→ filter Order has 2nd Product  = True  (ordinary, evaluates after context)
→ Bars: Order ID rows, Measure Names columns (Sales, Quantity), sorted by Sales
→ Order Detail: Customer Name / Order ID / Product Name, Measure Names columns
→ Viz in Tooltip on Bars embeds Order Detail filtered by Customer Name + Order ID
→ BANs: # ORDERS, % OF TOTAL ORDERS, AVG ORDER AMOUNT, AVG ORDER QUANTITY
```

The `{FIXED [Order ID]: MAX(...)}` calculation is the pivot. The set is boolean
(`In`/`Out`); `MAX` returns 1 when at least one line in that order is `In`, and
the result is stored against **every** line of the same Order ID. Filtering that
derived boolean to `True` therefore keeps all lines of qualifying orders.

`Order has 1st Products` is then added to **context** on the Bars and Order
Detail sheets, which forces Tableau to apply it before the second set is
evaluated. That is what restricts the second set control's value list to the
products that appear in the already-qualifying orders ("All Values in Context").
Without the context step the second control still lists every product, and
picking one that never co-occurs silently empties the view with no explanation.

The BANs sheet deliberately **omits** the context flag. `Total Orders =
{FIXED:COUNTD([Order ID])}` is a FIXED LOD, so a context filter would reduce it
to the qualifying-order count and make the percentage meaningless. Keeping stage
1 out of context on BANs leaves the denominator at all 5,009 orders, which is
exactly what the published default state shows (`5,009` / `100.0%` / `$459` / `8`).

## Required behavior

- **must-include-first-stage**: with a first product selected, only orders that
  contain that product survive, and each surviving order keeps its full
  line-item detail.
- **must-include-second-stage**: adding a second product restricts the result to
  orders that contain both products. The first flag is a context filter on Bars
  and Order Detail, so the second stage evaluates only inside the already-
  qualifying orders.
- **order-level-totals**: the Bars Sales/Quantity totals are order-level sums
  over all line items of each qualifying order, not just the matching lines.
- **bans-metrics**: `# ORDERS` counts distinct qualifying orders, `% OF TOTAL
  ORDERS` divides by the unfiltered `{FIXED:COUNTD([Order ID])}` (which stays
  global because stage 1 is not in context on BANs), and the two averages divide
  the qualifying orders' Sales/Quantity by `# ORDERS`.
- **order-detail-tooltip**: hovering a bar shows the embedded Order Detail
  worksheet restricted to that order's Customer Name and Order ID.

## Allowed visual differences

- The published dashboard is 1200×900. Fonts, exact spacing, banding and the
  decorative header/footer text may differ; the article's own requirement is to
  match formatting "as closely as possible", not pixel-perfectly.
- The replica keeps the default blue mark colour instead of the author's Nuriel
  Stone palette, and the Bars row height is slightly different.
- The two controls are native set controls in the author workbook. The
  replication renders them as dashboard filter controls (see `cwtwb baseline`);
  the underlying interactive semantics are equivalent for selection, but the
  dropdown widget identity is a known delta.

## cwtwb baseline

Tested released version: **0.27.1**. The case is a full `pass`: every required
primitive is supported by public APIs.

- `add_set(name, dimension, use_all=True)` creates the article's **"Use All"**
  sets (`<groupfilter function="level-members" user:ui-enumeration="all"/>`), so
  the default state keeps all 5,009 orders.
- `add_calculated_field` with `{FIXED [Order ID]: MAX([...])}` produces the
  order-level flags.
- `configure_chart(..., filters=[{"column": ..., "context": True}])` emits the
  `context="true"` attribute, which is exactly the Add-to-Context step.
- The `set_control` dashboard layout node renders native `setMembership` zones
  with `dropdown` / `checkdropdown` modes, a caption and an apply button.
- `configure_custom_tooltip(..., {"sheet": {...}})` emits a Viz-in-Tooltip run
  and the `VizInTooltipHideWorksheet` manifest entry.
- `configure_subtotals(..., subtotal_fields=[...], label="Grand Total")` gives
  the Order Detail sheet its labelled total row.

One real defect was found and fixed upstream while establishing this baseline:
`configure_chart(columns=["Measure Names"], measure_values=[...])` renders an
empty view because the virtual `Measure Names` field was registered as a
physical column and the `measure_values` request was dropped for primitive
marks. The case works around it by placing the two measures directly on the
columns shelf (the author's own structure), and the SDK fix is tracked
separately as `fix(sdk): honor measure values on primitive marks`.
