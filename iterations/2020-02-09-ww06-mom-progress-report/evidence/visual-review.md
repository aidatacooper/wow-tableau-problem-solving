# Cloud review: 2020 WW06

Decision: `replicated / acceptable_delta` within Cloud REST date-state, independent data and artifact-contract scope; not pixel identical.

Reviewed artifact SHA-256: `c5a02a25c1e0be73dec9b7587ac7ecebde0ef28ec8c651ec7e21e4ad47690fe4`.

All six paired PNGs were inspected for default November2019, December2019 and January2019. The three health columns are now separated by visible white gutters, so contiguous green/gray states remain distinguishable. Thicker health cells, bold category labels and separately aligned headings improve readability compared with the previously accepted thin-bar/grid baseline. Red incomplete-health dots and percentages remain visible, the month control is placed below the table, and restored attribution/link footer stays within the dashboard. No clipped or obscured category, health cell or control was observed.

| State | Author | Replica |
| --- | --- | --- |
| default | [image](../outputs/cloud-author.png) | [image](../outputs/cloud-replica.png) |
| december | [image](../outputs/cloud-author-december.png) | [image](../outputs/cloud-replica-december.png) |
| january | [image](../outputs/cloud-author-january.png) | [image](../outputs/cloud-replica-january.png) |

Independent verification recomputes monthly sales sums, distinct orders, units, current/prior ratios, three indicators and overall score for all17 subcategories. All six complete worksheet CSV exports pass across three month-pair states, covering1,326 displayed metric/indicator field instances. Currency and percentage comparisons respect each export?s displayed precision. January uses December2018 as prior month. The CSVs cover the entire health matrix; no button CSV is used.

Remaining differences: the table starts higher and its columns are slightly wider/shifted left relative to the author; bar height and vertical row spacing differ slightly; overall percentages use a lighter font and dots sit closer to the text. The parameter control is visibly exposed in the footer, while the author export omits its control card. Footer/link typography and SDK attribution differ. Green shades differ slightly from the author but follow the official requested palette. These affect presentation, while all category/health/score states agree.

The serialized tooltip contract carries the subcategory, current/prior month values and ratios; it is inspected without claiming hover execution. The parameter domain includes all48 extract months. REST states supply date parameters directly; no browser click or hover was executed. The locked Hyper and accepted workbook/image/CSV hashes are bound in the evidence. The artifact is frozen; use direct verification or metadata-only validation without rebuilding.
