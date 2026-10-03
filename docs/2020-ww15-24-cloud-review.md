# 2020 WW15–24 Cloud review

The next ten unused articles in publication order, April 10 through June 12, 2020, are complete. All ten are `replicated / acceptable_delta`; remaining visual differences are recorded per case and pixel matching is not claimed.

Acceptance covers **24 paired REST states, 48 images and 98 worksheet CSV files**. Data exports cover the worksheets listed below; a button export is never used as proof of an entire matrix. Raw-data oracles independently check calculations. Actions, event sources, targets and clearing behavior are checked in serialized artifacts. No browser click, hover or phone execution is claimed.

Every builder starts `TWBEditor("")` and uses public SDK APIs. The final zero-build audit copied only the builder, verifier, metadata and locked inputs into an empty directory with no author or replica workbook available. Author workbooks are analysis and comparison references, never templates. Comparison export copies only expose worksheet windows for full CSV exports; their provenance and source hashes are recorded. Accepted images, CSVs and workbook hashes are bound in each Cloud manifest. Use direct verifiers or `--metadata-only` to inspect accepted evidence; rebuilding requires fresh Cloud evidence.

| Case | Article date | Official challenge date | States / images / CSVs | Data scope and review |
| --- | --- | --- | --- | --- |
| 2020 WW15 | 2020-04-10 | 2020-04-08 | 4 / 8 / 8 | Four week-start states; complete date/category sales matrix and independent raw-sales oracle. Friday has one author date absent because it has no facts; the replica calendar preserves that zero cell. [Review](../iterations/2020-04-10-ww15-dynamic-week-start/evidence/visual-review.md) · [Manifest](../iterations/2020-04-10-ww15-dynamic-week-start/evidence/cloud-verification.json) |
| 2020 WW16 | 2020-04-17 | 2020-04-14 | 1 / 2 / 2 | All twelve months and nine pipeline/target measures per workbook: 216 exported cells, independently blended actuals and monthly targets. [Review](../iterations/2020-04-17-ww16-adjusted-target-missing-pipeline/evidence/visual-review.md) · [Manifest](../iterations/2020-04-17-ww16-adjusted-target-missing-pipeline/evidence/cloud-verification.json) |
| 2020 WW17 | 2020-04-25 | 2020-04-21 | 1 / 2 / 2 | All four regions and MTD/run-rate/plan values: 24 exported measures, independent weekday projection oracle. [Review](../iterations/2020-04-25-ww17-weekday-run-rate/evidence/visual-review.md) · [Manifest](../iterations/2020-04-25-ww17-weekday-run-rate/evidence/cloud-verification.json) |
| 2020 WW18 | 2020-05-03 | 2020-04-28 | 4 / 8 / 8 | Four Top-N/expansion states; complete product rows, weighted margins, native subtotals and grand totals, including rows beyond the visible viewport. [Review](../iterations/2020-05-03-ww18-most-profitable-products/evidence/visual-review.md) · [Manifest](../iterations/2020-05-03-ww18-most-profitable-products/evidence/cloud-verification.json) |
| 2020 WW19 | 2020-05-08 | 2020-05-05 | 3 / 6 / 6 | Weekly/daily/reset states: 52/14/52 date rows per workbook, title totals, averages and serialized drill/reset actions. [Review](../iterations/2020-05-08-ww19-dynamic-date-drilling/evidence/visual-review.md) · [Manifest](../iterations/2020-05-08-ww19-dynamic-date-drilling/evidence/cloud-verification.json) |
| 2020 WW20 | 2020-05-15 | 2020-05-12 | 3 / 6 / 30 | Three ordinary-filter states with stored selected-set membership; all Map, Sales, Orders, Customers and State List exports. Percent denominators, selected-state membership and global titles independently checked. [Review](../iterations/2020-05-15-ww20-state-contribution/evidence/visual-review.md) · [Manifest](../iterations/2020-05-15-ww20-state-contribution/evidence/cloud-verification.json) |
| 2020 WW21 | 2020-05-22 | 2020-05-19 | 1 / 2 / 12 | All six desktop worksheets: annual summaries/growth, monthly lines, Top 10 sales and Top/Bottom 10 profit products. Author data uses full calendar years despite its YTD caption. Automatic phone layout is verified as an artifact contract only. [Review](../iterations/2020-05-22-ww21-automatic-phone-layout/evidence/visual-review.md) · [Manifest](../iterations/2020-05-22-ww21-automatic-phone-layout/evidence/cloud-verification.json) |
| 2020 WW22 | 2020-05-29 | 2020-05-26 | 2 / 4 / 4 | Default and Chairs states; average review, budget, revenue and x/y vertex coordinates (profit and margin independently derived), native polygon paths and serialized set action contracts. [Review](../iterations/2020-05-29-ww22-profitability-budget/evidence/visual-review.md) · [Manifest](../iterations/2020-05-29-ww22-profitability-budget/evidence/cloud-verification.json) |
| 2020 WW23 | 2020-06-05 | 2020-06-02 | 1 / 2 / 2 | All 48 year/month bars, sales and actual PlotDate placement; the source leap-year date placement is preserved and documented. [Review](../iterations/2020-06-05-ww23-excel-style-bars/evidence/visual-review.md) · [Manifest](../iterations/2020-06-05-ww23-excel-style-bars/evidence/cloud-verification.json) |
| 2020 WW24 | 2020-06-12 | 2020-06-09 | 4 / 8 / 24 | Four county/window states; complete county table, daily bar/line and BAN exports. Independent raw-history oracle distinguishes full-history calculations from the chart date filter. CSV comparisons respect actual export precision; repeated scalar comparisons are not unique marks. [Review](../iterations/2020-06-12-ww24-moving-average-trend/evidence/visual-review.md) · [Manifest](../iterations/2020-06-12-ww24-moving-average-trend/evidence/cloud-verification.json) |

SDK enhancements cover native datasource blending, temporal set members, automatic weighted subtotals, Measure Names aliases, combined Top/Bottom sets, automatic phone layouts, discrete date domain completion, native set add/remove actions, qualified palettes and date-part filters, layered bar alignment, virtual reference axes and worksheet fit zoom. [Case-driven SDK changes](https://github.com/aidatacooper/cwtwb/blob/main/docs/case-driven-enhancements.md) documents the originating cases, generic APIs and synthetic regressions.

Final dependency: `cwtwb` 0.27.1 at `56377c5b170f0df1f5cd853fc483de26962dfed1`, installed from that exact Git commit rather than an editable checkout. SDK: **629 passed, 25 skipped**; shared case tests: **57 passed**. [Pinned SDK CI](https://github.com/aidatacooper/cwtwb/actions/runs/37121946903) passed. Earlier SDK runs and actual capability gaps remain recorded in each case. Some accepted renders were captured before the final SDK commit; their original artifacts remain frozen, while independent clean builds verify compatibility with the final pin. The catalogue contains **54 active cases** after this batch.

Functional and layout refinements include native weighted product subtotals, fully readable tables, weekday projections, correctly addressed contribution percentages, aligned top metrics and state sidebar, explicit Top/Bottom product groups, restored polygon geometry, axis-unit bar widths and complete moving-average data scopes. Remaining typography, spacing, map tone, line styling and annotation differences are documented per case.

## Default paired images

### 2020 WW15

| Author | Replica |
| --- | --- |
| ![Author WW15](../iterations/2020-04-10-ww15-dynamic-week-start/outputs/cloud-author.png) | ![Replica WW15](../iterations/2020-04-10-ww15-dynamic-week-start/outputs/cloud-replica.png) |

### 2020 WW16

| Author | Replica |
| --- | --- |
| ![Author WW16](../iterations/2020-04-17-ww16-adjusted-target-missing-pipeline/outputs/cloud-author.png) | ![Replica WW16](../iterations/2020-04-17-ww16-adjusted-target-missing-pipeline/outputs/cloud-replica.png) |

### 2020 WW17

| Author | Replica |
| --- | --- |
| ![Author WW17](../iterations/2020-04-25-ww17-weekday-run-rate/outputs/cloud-author.png) | ![Replica WW17](../iterations/2020-04-25-ww17-weekday-run-rate/outputs/cloud-replica.png) |

### 2020 WW18

| Author | Replica |
| --- | --- |
| ![Author WW18](../iterations/2020-05-03-ww18-most-profitable-products/outputs/cloud-author.png) | ![Replica WW18](../iterations/2020-05-03-ww18-most-profitable-products/outputs/cloud-replica.png) |

### 2020 WW19

| Author | Replica |
| --- | --- |
| ![Author WW19](../iterations/2020-05-08-ww19-dynamic-date-drilling/outputs/cloud-author.png) | ![Replica WW19](../iterations/2020-05-08-ww19-dynamic-date-drilling/outputs/cloud-replica.png) |

### 2020 WW20

| Author | Replica |
| --- | --- |
| ![Author WW20](../iterations/2020-05-15-ww20-state-contribution/outputs/cloud-author.png) | ![Replica WW20](../iterations/2020-05-15-ww20-state-contribution/outputs/cloud-replica.png) |

### 2020 WW21

| Author | Replica |
| --- | --- |
| ![Author WW21](../iterations/2020-05-22-ww21-automatic-phone-layout/outputs/cloud-author.png) | ![Replica WW21](../iterations/2020-05-22-ww21-automatic-phone-layout/outputs/cloud-replica.png) |

### 2020 WW22

| Author | Replica |
| --- | --- |
| ![Author WW22](../iterations/2020-05-29-ww22-profitability-budget/outputs/cloud-author.png) | ![Replica WW22](../iterations/2020-05-29-ww22-profitability-budget/outputs/cloud-replica.png) |

### 2020 WW23

| Author | Replica |
| --- | --- |
| ![Author WW23](../iterations/2020-06-05-ww23-excel-style-bars/outputs/cloud-author.png) | ![Replica WW23](../iterations/2020-06-05-ww23-excel-style-bars/outputs/cloud-replica.png) |

### 2020 WW24

| Author | Replica |
| --- | --- |
| ![Author WW24](../iterations/2020-06-12-ww24-moving-average-trend/outputs/cloud-author.png) | ![Replica WW24](../iterations/2020-06-12-ww24-moving-average-trend/outputs/cloud-replica.png) |
