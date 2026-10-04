# WW41 final Cloud review

Decision: **acceptable_delta**. Reviewed the complete paired default, Profit Ratio and Items Per Order PNGs and independently verified all 24 worksheet CSVs. This review binds the accepted TWBX SHA-256 `c97e5fb4332a42b941be9de3c7a23899f4d8880e729055275c0afe097322e420` to `evidence/cloud-verification.json` and its individual image/data hashes. Tested with cwtwb 0.27.1, exact Git commit `eb1380d5da9c1b1bf1b306128cb8397150ba1a53`.

| REST state | Original | Replica | Ranked cards, first to third |
| --- | --- | --- | --- |
| Sales Per Order | [Image](../outputs/cloud-author.png) | [Image](../outputs/cloud-replica.png) | Technology $542; Furniture $421; Office Supplies $192 |
| Profit Ratio | [Image](../outputs/cloud-author-profit-ratio.png) | [Image](../outputs/cloud-replica-profit-ratio.png) | Technology 17.4%; Office Supplies 17.0%; Furniture 2.5% |
| Items Per Order | [Image](../outputs/cloud-author-items-per-order.png) | [Image](../outputs/cloud-replica-items-per-order.png) | Office Supplies 6.12; Furniture 4.55; Technology 4.49 |

All three cards fill their intended dashboard areas with complete readable white text. The metric choice updates the title, vertical metric label, dollar/percent units, line values and ranking order. All six extrema labels are visible in each replica state, including Technology $401 in the default state. No card clipping, missing card, stray 0.5000 label or internal parameter reference remains.

The independent oracle reads all 9994 original order lines. Each Line export must cover every one of the 48 quarter/category data points **and** all 48 quarter/category reference values. References equally average the sixteen rounded quarter metrics for each category: default Furniture 423.875, Office Supplies 195.0625 and Technology 567.125. Native rank cards have no quarter grain; their values independently aggregate the full category facts and use the original rounding rules. These are deliberately checked separately from the quarterly reference averages. All three parameter states, both roles and four worksheet exports per role are mandatory; empty business CSVs, omitted reference fields, partial states and missing reference values fail. Dynamic replica metric labels and both roles' dollar/percent suffixes are also checked against the requested parameter.

Remaining visual differences are small and visible: replica reference labels are black and positioned slightly below or apart from their coloured dotted lines, whereas the original labels match category colours and sit above the lines; the original Profit Ratio reference captions overlap more closely. Replica line and dot strokes are thinner. Automatic six-month ticks begin at Q2/Q4 rather than the original Q1/Q3 pattern, and plot endpoints/axis padding, typography and footer credit placement differ. These do not change the data, reference values, ranking, units or readability. This is not a pixel-identical result.

Acceptance uses Cloud REST parameter states, full worksheet CSVs and generated-workbook contracts. No browser dropdown clicks, hover events or tooltip execution are claimed. The original comparison package only exposes the existing worksheet windows; provenance binds its original and export hashes. Failed de89 captures were archived under `scratch/ww41-analysis/failed-de89-cloud` and are not accepted evidence.
