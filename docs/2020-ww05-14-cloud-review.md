# 2020 WW05–14 Cloud review

The next ten unused articles in publication order, from February 2 to April 4, 2020, are complete. Each case is `replicated / acceptable_delta`; pixel matching is not claimed.

Acceptance covers **30 paired REST states, 60 images and 126 worksheet CSV files**. WW05 has one intentionally empty author Advanced export; it is excluded from data proof and replaced by two full author reference worksheets. Actions, sources, targets, clearing behavior, tooltips and native toggles are checked in serialized artifacts. No browser click or hover was executed.

Every builder starts `TWBEditor("")` and uses public SDK APIs with locked extracted data. Original workbooks are analysis/publication references, never build templates. Accepted workbook and image/CSV hashes are bound in each cloud-verification.json. Rebuilding changes identity: use the verifier or `--metadata-only` for existing evidence.

| Case | Article date | Official challenge date | Declared data scope and review |
| --- | --- | --- | --- |
| 2020 WW05 | 2020-02-02 | 2020-01-28 | 48 region/month ranks on both axes and eight endpoint labels; author Advanced CSV is empty, so Basic Data/Data Labels supply the independently checked reference. [Review](../iterations/2020-02-02-ww05-regions-rank-month-to-month/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-02-02-ww05-regions-rank-month-to-month/evidence/cloud-verification.json) |
| 2020 WW06 | 2020-02-09 | 2020-02-04 | All 17 subcategories, three month-pair states and thirteen health/indicator values per row (1,326 checked field instances). [Review](../iterations/2020-02-09-ww06-mom-progress-report/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-02-09-ww06-mom-progress-report/evidence/cloud-verification.json) |
| 2020 WW07 | 2020-02-16 | 2020-02-11 | Three categories and six forecast/target/reset states; full Viz measures and signed formatted replica label strings. [Review](../iterations/2020-02-16-ww07-forecast-target-parameters/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-02-16-ww07-forecast-target-parameters/evidence/cloud-verification.json) |
| 2020 WW08 | 2020-02-22 | 2020-02-18 | All member profiles and complete concatenated lists for BMI, All, Flu and physician/age states; full Report exports, not the visible scrolled page. [Review](../iterations/2020-02-22-ww08-concatenated-list/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-02-22-ww08-concatenated-list/evidence/cloud-verification.json) |
| 2020 WW09 | 2020-02-29 | 2020-02-25 | All 5,009 order events, 793 customer profiles, previous-order dates, same-day edge cases, all connection-interval endpoints and two global KPIs; default and Noel states. [Review](../iterations/2020-02-29-ww09-90-day-reorder/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-02-29-ww09-90-day-reorder/evidence/cloud-verification.json) |
| 2020 WW10 | 2020-03-07 | 2020-03-03 | All 17 hotel/pub pairs, 32 distinct pubs and 10 hotels across five map/hotel/radius/sort states; independent distance oracle, serialized buffer/tooltip/actions. [Review](../iterations/2020-03-07-ww10-spatial-buffers/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-03-07-ww10-spatial-buffers/evidence/cloud-verification.json) |
| 2020 WW11 | 2020-03-13 | 2020-03-10 | Sales, orders and quantity for 12/13/12 dates across three selected-date states; tied unique-rank ordering differences are explicitly recorded. [Review](../iterations/2020-03-13-ww11-smart-ranked-lists/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-03-13-ww11-smart-ranked-lists/evidence/cloud-verification.json) |
| 2020 WW12 | 2020-03-21 | 2020-03-17 | 81 weekly, 156 daily, 24 monthly/two-year and 48 monthly/four-year date marks; order count/profit/size plus all 17 selector-domain entries. [Review](../iterations/2020-03-21-ww12-missing-periods-autosize-bars/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-03-21-ww12-missing-periods-autosize-bars/evidence/cloud-verification.json) |
| 2020 WW13 | 2020-03-28 | 2020-03-24 | Runtime Date CSV, ten KPI calculations and 22 Sales plus 22 Profit monthly marks per workbook; preserved TODAY behavior, no fixed March-date claim. [Review](../iterations/2020-03-28-ww13-simple-sales-dashboard/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-03-28-ww13-simple-sales-dashboard/evidence/cloud-verification.json) |
| 2020 WW14 | 2020-04-04 | 2020-03-31 | Full six-stage Data worksheet: current/cumulative/window/closed/ratio values, checked from raw Hyper; plotted field references and native dual-axis contracts. [Review](../iterations/2020-04-04-ww14-sales-pipeline/evidence/visual-review.md) · [Hash-bound exports](../iterations/2020-04-04-ww14-sales-pipeline/evidence/cloud-verification.json) |

SDK enhancements include independent Hyper sources, sheet tooltips, native collapsible containers, overlaid measure palettes and widths, adaptive axis-unit bar sizing, ordinal/null shapes, qualified table-calculation addressing, repeated-axis pane identities and unique mixed-action names. [SDK changes and source cases](https://github.com/aidatacooper/cwtwb/blob/main/docs/case-driven-enhancements.md) records the problems and synthetic regressions.

Final dependency: `cwtwb` 0.27.1 at the exact Git commit in requirements.txt. SDK: **575 passed, 25 skipped**; shared case tests: **55 passed**. The pinned SDK CI and actual commit are recorded in every sdk-polish-validation.json. Case catalogue contains **44 active cases** after this batch.

## Layout refinement

All ten cases were refined after the initial acceptance. The current evidence is a new Cloud capture bound to the polished workbooks. Improvements include region-chart spacing, separated health-indicator columns, aligned forecast/target side panels, readable concatenated-list controls, larger reorder KPIs and finer connections, compact map legends including the restored size scale, grouped below-average rank shading, native hidden-panel framing, sales dashboard sections and aligned pipeline rows. The reorder filter keeps a stable white/gray layout instead of reproducing the author filtered view?s large magenta empty area. Remaining differences are explicitly reviewed per case; no pixel-level match or browser interaction is claimed. Previous SDK run records are retained, and each polish-baseline.json links the immutable pre-polish evidence in Git history.

## Default paired images

The full state-by-state findings and remaining deltas are in the per-case reviews above.

### 2020 WW05

| Author | Replica |
| --- | --- |
| ![WW05 author](../iterations/2020-02-02-ww05-regions-rank-month-to-month/outputs/cloud-author.png) | ![WW05 replica](../iterations/2020-02-02-ww05-regions-rank-month-to-month/outputs/cloud-replica.png) |

### 2020 WW06

| Author | Replica |
| --- | --- |
| ![WW06 author](../iterations/2020-02-09-ww06-mom-progress-report/outputs/cloud-author.png) | ![WW06 replica](../iterations/2020-02-09-ww06-mom-progress-report/outputs/cloud-replica.png) |

### 2020 WW07

| Author | Replica |
| --- | --- |
| ![WW07 author](../iterations/2020-02-16-ww07-forecast-target-parameters/outputs/cloud-author.png) | ![WW07 replica](../iterations/2020-02-16-ww07-forecast-target-parameters/outputs/cloud-replica.png) |

### 2020 WW08

| Author | Replica |
| --- | --- |
| ![WW08 author](../iterations/2020-02-22-ww08-concatenated-list/outputs/cloud-author.png) | ![WW08 replica](../iterations/2020-02-22-ww08-concatenated-list/outputs/cloud-replica.png) |

### 2020 WW09

| Author | Replica |
| --- | --- |
| ![WW09 author](../iterations/2020-02-29-ww09-90-day-reorder/outputs/cloud-author.png) | ![WW09 replica](../iterations/2020-02-29-ww09-90-day-reorder/outputs/cloud-replica.png) |

### 2020 WW10

| Author | Replica |
| --- | --- |
| ![WW10 author](../iterations/2020-03-07-ww10-spatial-buffers/outputs/cloud-author.png) | ![WW10 replica](../iterations/2020-03-07-ww10-spatial-buffers/outputs/cloud-replica.png) |

### 2020 WW11

| Author | Replica |
| --- | --- |
| ![WW11 author](../iterations/2020-03-13-ww11-smart-ranked-lists/outputs/cloud-author.png) | ![WW11 replica](../iterations/2020-03-13-ww11-smart-ranked-lists/outputs/cloud-replica.png) |

### 2020 WW12

| Author | Replica |
| --- | --- |
| ![WW12 author](../iterations/2020-03-21-ww12-missing-periods-autosize-bars/outputs/cloud-author.png) | ![WW12 replica](../iterations/2020-03-21-ww12-missing-periods-autosize-bars/outputs/cloud-replica.png) |

### 2020 WW13

| Author | Replica |
| --- | --- |
| ![WW13 author](../iterations/2020-03-28-ww13-simple-sales-dashboard/outputs/cloud-author.png) | ![WW13 replica](../iterations/2020-03-28-ww13-simple-sales-dashboard/outputs/cloud-replica.png) |

### 2020 WW14

| Author | Replica |
| --- | --- |
| ![WW14 author](../iterations/2020-04-04-ww14-sales-pipeline/outputs/cloud-author.png) | ![WW14 replica](../iterations/2020-04-04-ww14-sales-pipeline/outputs/cloud-replica.png) |
