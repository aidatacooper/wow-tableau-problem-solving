# Cloud review: Intermediate dynamic heatmap

Result: **acceptable_delta**. Reviewed all eight paired1800×1000 PNGs and all eight full `Chart-Int` REST CSVs for workbook SHA256 `1343cfaad594d40473768073eb61ba4fefea5d0f9c8d13a350dd0145152099b0`. The manifest binds the replica, the analysis-only author comparison, and every exported PNG/CSV. The author comparison changes worksheet-window visibility only; provenance verifies its calculations, layouts, actions and data are unchanged.

| REST state | Cells per workbook CSV | Native totals per CSV | Visible label behavior |
| --- | ---: | ---: | --- |
| Default |65|17|48 interior labels empty; four year totals, twelve month totals and grand total visible. |
| Year2019 |26|14|One year remains; SIZE Years=1 makes all thirteen columns display the total-label branch. |
| January |10|6|One month remains; SIZE Months=1 makes each year and total cell display the total-label branch. |
| Year2019 +January |4|3|The one interior cell and three native totals all display3.85. |

The independent verifier checks all210 paired CSV records against9994 locked original Superstore order-line records, including all65 default cells. Quantity retains the same nine-decimal export precision as the author; Total Label displays two decimals and Profit Ratio whole percentage points. The verifier accounts for actual export rounding. It independently distinguishes the colour's equal-cell visual average from the label's weighted raw-record average:2016's twelve-month visual average is3.7752638356, while its total label is based on3.8038133467 and displays3.80. Every exported Total Label, Cell Label, AVG Quantity and Profit Ratio is checked; CSV totals are identified by Tableau's `All` member rather than inferred from a button export.

The restored root8px and leaf4px margins align the matrix, legend, total whitespace and month/year headers with the original across all states. The complete January–December order, teal-blue colour scale, white total separators and every visible number remain intact. Remaining visual differences are text details: the title sits about10px lower at dashboard scale, the Average Quantity Sold caption uses darker/smaller text, footer credit weights differ, and the source's underlined link is plain blue text. These do not hide matrix values or controls. In the single-cell state, both source and replica retain the source layout limitation where the collapsed continuous legend's lone3.85 caption is clipped beneath its bar; all four actual heatmap labels and their CSV values remain complete.

Two native on-hover assign actions, their Chart-Int source, separate month/year target sets and exclude-all clearing behavior are verified in the generated artifact. Nested SIZE calculations address years and months separately. Both stored sets are empty during REST exports. Independent formula-oracle scenarios check empty selection, one selected cell and a two-month/two-year intersection. **No browser hover/click event was executed or claimed.** Ordinary REST filters demonstrate the SIZE=1 branches only. Donna's unresolved Advanced click-row/column dashboard is outside the Intermediate acceptance scope.

The exact released SDK56377 baseline was separately imported from a Git archive and passed the same empty-workbook public-API builder plus raw-data/artifact verification (`sdk-baseline.json`); that separate baseline artifact was not Cloud-published. Current Cloud evidence is bound only to the replica hash above. No reconstruction occurred after this capture.
