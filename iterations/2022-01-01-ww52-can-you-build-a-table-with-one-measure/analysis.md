# WW52 — Can you build a table with one measure?

## The business question

Luke Stanke's final 2021 challenge: present a crosstab of Sales by
Category / Sub-Category across months in which **one** measure simultaneously
shows

* the actual sales value in every detail cell, and
* that Category's **share of the month's total** on each Category subtotal row,

while the whole table is coloured with the green–blue–white diverging palette
so the shares read as green and the money reads as (very pale) blue.

The point is not the numbers — it is that Tableau's table calculations can tell
a single measure which of two quantities to emit depending on *where* the mark
sits in the view.

## Source material

| Item | Value |
| --- | --- |
| Article | `posts/2022-01-01-Can_you_build_a_table_with_one_measure.html` (published 2022-01-01T19:30:19Z) |
| Official challenge | <https://www.workout-wednesday.com/wow2021_w52/>, WordPress post 6578, published 2021-12-28 |
| Author workbook | `2021_12_29_WW52_SingleTable_OneMeasure.twbx` (sha256 in `inputs/source-lock.json`) |
| Extract | `federated_0g0c07z1rhpm3o1en8fhr0.hyper`, 9,994 rows, columns `Order Date`, `Category`, `Sub-Category`, `Sales` |

The workbook contains one worksheet (`Table`) and one fixed-size dashboard
(1000 × 600) that holds that worksheet plus four 8pt footer text zones.

## What the author built (analysis-only reading of the author TWB)

Two calculations, both table calculations with the default `ordering-type="Rows"`:

```
Size            = SIZE()
Custom Measure  = IF [Size] = 1
                  THEN SUM(Sales)
                  ELSE -SUM(Sales)/TOTAL(SUM(Sales))
                  END
```

Both are re-addressed **compute using Category** at the worksheet level
(`<table-calc ordering-field="[ds].[none:Category:nk]" ordering-type="Field"/>`,
plus a nested `field=` entry for `Size` inside the Custom Measure instance).

That single addressing decision is the whole trick. The view is
`MONTH(Order Date)` on Columns and `Category / Sub-Category` on Rows with
Category subtotals and grand totals enabled. Tableau partitions a table
calculation by every dimension that is *not* in its addressing, so with
Category as the addressing field:

| Cell | Partition | `SIZE()` | Branch taken |
| --- | --- | --- | --- |
| detail (Category × Sub-Category × month) | one mark per month and sub-category | 1 | `SUM(Sales)` |
| Category subtotal (month) | the three Category marks of that month | 3 | `-SUM(Sales)/TOTAL(SUM(Sales))` |
| grand total (month) | the single grand-total mark of that month | 1 | `SUM(Sales)` |

`TOTAL(SUM(Sales))` inside the subtotal partition sums the three category
subtotals, i.e. the month's grand total, so the share is exactly
`category month sales ÷ month total`. A spot check against the extract:
Furniture January 31,569.07 / 94,924.84 = 0.3326 → the 33% the author prints.

The **negative** sign in the `ELSE` branch is deliberate: the diverging palette
is centred on 0, so shares land on the green half while money lands on the
white/blue half. A `0%;0%` number format on the subtotal class hides the sign.

Remaining author formatting, all reproduced:

| Element | Author XML |
| --- | --- |
| Rows shelf | `(<Category> / <Sub-Category>)` with `total="true" onTop="true"` |
| Subtotals | `<subtotals><column>[none:Category:nk]</column></subtotals>` |
| Cell formats | default and `data-class="total"` → `c"$"#,##0;-"$"#,##0`; `data-class="subtotal"` → `*0%;0%` |
| Header labels | `total-label` `data-class="total"` on Category → `Total`; `data-class="subtotal"` on Sub-Category → `% of Total` |
| Colour | `<encoding attr="color" type="interpolated" palette="green_blue_white_diverging_10_0" center="0.0" include-totals="true"/>` |
| Marks | `Square`, text + colour both bound to Custom Measure, labels shown |
| Grid | `display-field-labels scope="cols" value="false"`, `div-level scope="cols" value="1"`, cell `width="127"` |

## Replication design

`build_replication.py` starts from `TWBEditor("")` and uses only public SDK
calls: `set_hyper_connection`, `add_calculated_field`, `add_worksheet`,
`configure_chart`, `set_worksheet_rich_title`, `configure_subtotals`,
`configure_worksheet_style`, `add_dashboard`, then `save`.

Two things needed more than a single call:

1. **Totals on top.** `configure_worksheet_style(show_row_totals=True)` writes
   `<rows total="true">` but there is no API for `onTop`, which is what puts
   the grand total and each subtotal *above* its group. The builder therefore
   round-trips the workbook it just wrote through the documented native-JSON
   representation (`convert_workbook` → patch one attribute → `convert_workbook`)
   and sets `onTop="true"` on its own rows shelf. No author file is read.
2. **Subtotal label placement.** Tableau stores the subtotal label against the
   column that *displays* it (Sub-Category), while `configure_subtotals`
   attaches its `label` argument to the subtotaled field (Category). The label
   is therefore added with `configure_worksheet_style(header_formats=...)`
   scoped to Sub-Category; the extra Category-scoped format that
   `configure_subtotals` leaves behind is inert (Cloud renders the
   Sub-Category label).

Two other details worth recording:

* `color_style` rejects `symmetric`; the author's `symmetric="false"` is
  Tableau's default and is simply omitted.
* `table_calc_overrides(ordering_field=...)` emits the bare column reference
  `[ds].[Category]` for a non-derived dimension where Tableau's UI writes the
  instance name `[ds].[none:Category:nk]`. Both resolve to the same partition:
  the exported values match the author's export cell for cell.
* The worksheet zone needs `fit="entire"`: the author's fixed 127px cells
  overflow a 1000px dashboard otherwise, and Tableau scales them down to ~68px
  exactly as the author's view does.

## Acceptance scenarios

| id | Scenario | Mode |
| --- | --- | --- |
| `single-measure-encoding` | Text and Colour both bind one and the same calculated measure; raw `Sales` is not on the Text shelf; mark is Square | automated |
| `size-driven-subtotal-split` | `Size = SIZE()`; `Custom Measure` is `IF Size = 1 THEN SUM(Sales) ELSE -SUM(Sales)/TOTAL(SUM(Sales))`; both table calculations compute using Category | automated |
| `totals-above-groups` | Rows shelf nests Category over Sub-Category with `total="true"` and `onTop="true"`; Category is in `<subtotals>`; columns use month of Order Date | automated |
| `subtotal-labels-and-formats` | Grand total label `Total`, subtotal label `% of Total`, currency for detail and grand total, `0%;0%` for subtotals | automated |
| `diverging-colour-scale` | Interpolated `green_blue_white_diverging_10_0` centred on 0, range includes totals, bound to the same measure | automated |
| `dashboard-fixed-size` | 1000 × 600 fixed dashboard holding the table plus four footer text zones | automated |
| `subtotal-share-oracle` | Every cell is recomputed from the extracted facts (detail = SUM(Sales), subtotal = −category/month total, grand total = month total) and compared with the captured Tableau exports | automated |
| `replica-export-parity` | The replica's exported worksheet equals the author's exported worksheet cell for cell | automated |

## cwtwb result

`pass` for the technique itself — the two calculated fields, the Category
table-calculation addressing, the per-data-class number formats, the
`total-label` scopes, the diverging palette with `include-totals`, subtotals and
the fixed-size dashboard are all public API.

`workaround` for two structural details that have no public setter:

* `totals-placement` — no API writes `onTop`; solved with the documented
  native-JSON round trip.
* `subtotal-label-field` — `configure_subtotals` couples the subtotaled field
  list with the label field, so the author's label placement needs a second
  `header_formats` call and leaves one inert format behind.

## Visual comparison

`outputs/cloud-author.png` and `outputs/cloud-replica.png` are the same REST
image request against the published author workbook and the replica. The
replica reproduces the grand total row above each group, the `% of Total`
subtotal rows, the green/white/blue shading and the footer strip. Measured
geometry differs by about 1–3% (month column pitch 138px vs 136px at 2×;
table height 923px vs 895px) because Tableau's "Entire View" scaling reacts to
the tiny difference in title/zone padding. The right-hand footer reads
`RECREATED BY : CW TWB` instead of the author's name.
