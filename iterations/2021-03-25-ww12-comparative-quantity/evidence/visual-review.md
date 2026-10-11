# Visual review — WW12 Comparative Quantity Analysis

## Scope

Two Cloud REST captures were taken at the default state
(`pSelectedSubCat = "Fasteners"`):

- `outputs/cloud-author.png` — the author's published dashboard view
  (`2021_03_24_WW12_Comparative_Qty`).
- `outputs/cloud-replica.png` — the replica worksheet (`Viz`) in the same state.

The published author workbook exposes the dashboard and a `Data` debugging
sheet; the dashboard is the published artefact, so it is the comparison target.

## Result: acceptable_delta

The business answer is identical. The replica reproduces:

- one bar per Sub-Category in both panels, sorted by the average quantity
  descending (Binders → Machines);
- the manufacturer-inclusive average on the left with the selected Sub-Category
  (Fasteners) highlighted teal and all others neutral grey;
- the variance panel on the right with a diverging orange/blue palette centred
  on zero, transparent to roughly 75%;
- the axis titles "Avg. Total Quantity inclusive of Manufacturer" and
  "Variance".

The Cloud CSV exports agree to the digit on the business values: the replica's
`Avg Qty Inc Manufacturer` and `Variance` columns equal the author's
`Avg Qty`/`Variance` values (e.g. Binders 284.476190476 / +132.142857143,
Machines 22 / −130.333333333, Fasteners 152.333333333 / 0).

## Allowed differences

- The author's `Avg Qty` pill carries a rounded display format
  (`n#,##0;-#,##0`), so the author's export shows `135` where the replica shows
  `135.272727273`. The underlying values and the variance are identical; this is
  number formatting, not a data difference.
- The replica sheet title reads `Viz`; the author's dashboard shows a rich title
  ("Subcategory Comparative Quantity Analysis" / "inclusive of manufacturer").
  Titles are decorative.
- Exact fonts, padding and the header/footer text zones differ.
- The author's extra `Data` debugging sheet is not reproduced.
