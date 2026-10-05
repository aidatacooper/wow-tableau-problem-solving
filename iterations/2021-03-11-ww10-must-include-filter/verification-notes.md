# Independent verification — 2021 WW10 "must include" filter

The locked input hash matches `inputs/source-lock.json`: 9,994 lines and 5,009
distinct orders. Verification reads only the locked extract, the written case
files and the built TWBX. It never opens the author workbook or imports the
builder. Exact machine-readable evidence lives in
`outputs/independent-verification.json`; the runnable check is
`verify_replication.py`.

## Locked-data oracle

`outputs/data-oracle.json` contains complete qualifying order sets, customer
names, full-order Sales/Quantity totals, sample orders and BAN values. Product
pairs were discovered from the data, with independent SQL `HAVING` checks of the
Python set-intersection counts.

| Product 1 | Product 2 | Qualifying orders |
| --- | --- | ---: |
| Acco D-Ring Binder w/DublLock | I Need's 3d Hello Kitty Hybrid Silicone Case Cover… | 2 |
| Acco Hanging Data Binders | Newell 315 | 2 |
| Acco Hot Clips Clips to Go | Flat Face Poster Frame | 2 |
| "While you Were Out" Message Book… | #10 Gummed Flap White Envelopes, 100/Box | 0 |

The first pair includes order `CA-2017-129147` (Liz Carlisle): Sales
609.438, Quantity 16, **three** lines of which one is neither selected product.
That extra line is the point of the case — the order-level totals must include
it. The fixture keeps the input's floating-point precision rather than rounding
to currency display precision.

## Functional (Cloud REST) evidence

`evidence/functional-verification.json` records a real two-stage execution: the
two sets were pre-populated with one product each, published, and exported over
REST.

- Bars returned exactly `CA-2017-129147` and `US-2017-103905` — the oracle's two
  qualifying orders, and no others.
- BANs returned `# ORDERS = 2`, `% OF TOTAL ORDERS = 0.000399281`,
  `AVG ORDER AMOUNT = 338.821`, `AVG ORDER QUANTITY = 13.5`, matching the oracle.

This proves the intersection semantics and the order-level aggregation, not just
the presence of XML nodes.

## Structural acceptance checks

All checks pass in `verify_replication.py`:

| Check | Result |
| --- | --- |
| Both sets exist as `filter-group` sets with member conditions | PASS |
| Both `{FIXED [Order ID]: MAX([set])}` boolean flags | PASS |
| Stage-1 flag is `context="true"` on Bars and Order Detail | PASS |
| Stage-1 flag is **not** context on BANs (keeps the global denominator) | PASS |
| Stage-2 flag is an ordinary filter on all three sheets | PASS |
| No line-level product filter shrinks the totals | PASS |
| Bars binds `SUM(Sales)` and `SUM(Quantity)` on the shelves | PASS |
| `# ORDERS`, both averages divide by `# ORDERS` | PASS |
| `Total Orders = {FIXED:COUNTD([Order ID])}` and the percentage divides by it once | PASS |
| BANs exposes exactly the four requested metrics | PASS |
| Bars tooltip embeds `Order Detail` filtered by Customer + Order ID | PASS |
| `Order Detail` is hidden and listed in the viz-in-tooltip manifest | PASS |
| Captured default-state BANs CSV matches the locked-data oracle | PASS |

## Reusable cwtwb findings

One real released-SDK defect was found while establishing the baseline. It is
recorded here and fixed upstream rather than worked around silently.

**`configure_chart(measure_values=...)` produces an empty view on primitive
marks.** The minimal reproducer
`configure_chart("V", mark_type="Text", columns=["Measure Names"], measure_values=["SUM(Sales)","SUM(Quantity)"])`
publishes without error but every worksheet export is empty. Two distinct causes
were isolated:

1. A literal `"Measure Names"` encoding registered a bogus physical
   `[Measure Names]` datasource column instead of the virtual
   `[:Measure Names]` field, so Tableau could not resolve the color.
2. `configure_chart` accepted `measure_values` but dropped it when routing to
   `BasicChartBuilder` (Bar/Line/Circle/Square), leaving the measure shelf empty.

The case binds the two measures directly on the columns shelf (the author's own
structure) and the SDK fix is `fix(sdk): honor measure values on primitive
marks`.

The other primitives the case needs are fully supported and were used as
documented: `add_set(use_all=True)`, the `set_control` dashboard node,
`context=True` filters, viz-in-tooltip sheet runs and `configure_subtotals`.

## Visual review

`outputs/cloud-author.png` and `outputs/cloud-replica.png` are the dashboard
default states for both roles. The BAN values match exactly
(`5,009` / `100.0%` / `$459` / `8`), and both native set controls read `All`.
Remaining differences are cosmetic: the replica keeps the default blue mark
colour instead of the author's Nuriel Stone palette, and has minor spacing and
row-height differences. None of these change the business answer.
