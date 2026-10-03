# Cloud visual and data review ? 2020 WW20

Accepted within the documented scope as `acceptable_delta`. Reviewed artifact SHA256: `0d4e7ef4677364fad92333f9449498d7ed26c39cf6da207913c79b8416964482`. The independent verifier passes with released SDK `56377c5b170f0df1f5cd853fc483de26962dfed1`.

All six paired REST images were inspected after the layout refinement. The three contribution metrics are at the top, aligned on the same baseline with visible 0?100% scales. Selected contributions are purple on the left, followed by gray remainders. The source-width left map and the separate gray right removal sidebar preserve the original hierarchy. Sidebar state names are readable white labels on purple marks; all four names are visible in the default and selected-only states, and Alabama is visible alone in the Alabama state. The customer axis has no unintended calculation title, and all three scales show 0, 20, 40, 60, 80 and 100 percent.

| REST state | Paired images | Complete map rows per workbook | Selected-list members per workbook |
| --- | --- | --- | --- |
| Default | [Author](../outputs/cloud-author.png), [replica](../outputs/cloud-replica.png) | 49 | 4 |
| Selected-only ordinary State filter | [Author](../outputs/cloud-author-selected-only.png), [replica](../outputs/cloud-replica-selected-only.png) | 4 | 4 |
| Alabama ordinary State filter | [Author](../outputs/cloud-author-alabama.png), [replica](../outputs/cloud-replica-alabama.png) | 1 | 1 |

The [CSV comparison](cloud-data-comparison.json) passes all 30 complete worksheet exports: five sheets ? two workbooks ? three states. This includes 108 map rows with sales, distinct orders and distinct customers checked independently, 18 selected-list rows, 8 Sales contribution marks, 8 Orders contribution marks, and 12 customer-pane records. The locked 9,994-row original Hyper is the oracle. The default selected states total sales 206,905.211, 486 distinct orders and 369 distinct customers; the full dataset has 793 distinct customers, so the global customer share is 46.5% after display rounding. Customers are counted distinctly across states, rather than added from per-state counts.

The ordinary REST State filters change visible Sales/Orders contributions to 100% in the filtered states, while the FIXED selected-share headings and customer share retain their global denominators, matching the reference. Those filters do not mutate the selected set. The [functional verifier](functional-verification.json) separately checks native map-add and list-remove set action sources, on-select events, add/remove modes and do-nothing clearing, plus the True-to-False map deselection action. Additional set outcomes are independently computed; they are not claims of executed browser actions. Complete map and contribution CSVs establish numerical scope; a removal-button or list CSV alone cannot establish the whole map or percentages.

Remaining visual differences are thinner percentage bars, lighter map fills and a slightly smaller geographic extent within the same map region, regular rather than italic title typography, and modest instruction/footer spacing and alignment differences. A faint map frame remains. The source and replica retain the same information order and functional regions; no metric, axis label, map state or removal label is hidden. The result is not pixel-identical.

Acceptance uses Cloud REST images/data plus workbook contracts. No browser click or hover was executed or claimed. The reference export changes only hidden worksheet-window flags; [export provenance](export-provenance.json) records that transformation. Earlier layout/axis captures were superseded and archived in scratch, rather than treated as final visual acceptance.
