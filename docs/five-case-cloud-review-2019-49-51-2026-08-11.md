# Five-case Cloud review: 2019 WW49-51 and 2026 WW08/11

This batch independently rebuilds five Workout Wednesday workbooks from `TWBEditor("")`, using public cwtwb APIs and preserved input data. Author TWB/TWBX files are analysis and comparison sources only. The two business dates are article publication date and official challenge date; challenge year/week identify the case.

Acceptance is actual Tableau Cloud REST rendering and exported parameter/filter/data states, independent Hyper calculations, and serialized artifact contracts. No browser clicks, selections, resets or hovers were executed or claimed. `acceptable_delta` means the documented differences were accepted within that scope; it does not mean pixel-identical reproduction.

## Current acceptance and source identity

| Case | Article date | Official challenge date | Status | Detailed evidence |
| --- | --- | --- | --- | --- |
| [2019 WW49: swap states](https://donnacoles.home.blog/2019/12/08/can-you-swap-states/) | 2019-12-08 | 2019-12-03 | replicated / acceptable_delta / verified | [Review](../iterations/2019-12-08-ww49-swap-states/evidence/visual-review.md), [receipt](../iterations/2019-12-08-ww49-swap-states/evidence/cloud-verification.json) |
| [2019 WW50: retention heatmap](https://donnacoles.home.blog/2019/12/15/can-you-build-a-retention-heat-map-with-a-marginal-histogram/) | 2019-12-15 | 2019-12-11 | replicated / acceptable_delta / verified | [Review](../iterations/2019-12-15-ww50-retention-heatmap/evidence/visual-review.md), [receipt](../iterations/2019-12-15-ww50-retention-heatmap/evidence/cloud-verification.json) |
| [2019 WW51: sales performance](https://donnacoles.home.blog/2019/12/23/sales-performance-dashboard/) | 2019-12-23 | 2019-12-18 | replicated / acceptable_delta / verified | [Review](../iterations/2019-12-23-ww51-sales-performance-dashboard/evidence/visual-review.md), [receipt](../iterations/2019-12-23-ww51-sales-performance-dashboard/evidence/cloud-verification.json) |
| [2026 WW08: dynamic visibility and filter actions](https://donnacoles.home.blog/2026/03/01/dzv-filter-actions/) | 2026-03-01 | 2026-02-26 | replicated / acceptable_delta / verified | [Review](../iterations/2026-03-01-ww08-dzv-filter-actions/evidence/visual-review.md), [receipt](../iterations/2026-03-01-ww08-dzv-filter-actions/evidence/cloud-verification.json) |
| [2026 WW11: layout containers](https://donnacoles.home.blog/2026/03/23/can-you-use-layout-containers/) | 2026-03-23 | 2026-03-17 | replicated / acceptable_delta / verified | [Review](../iterations/2026-03-23-ww11-layout-containers/evidence/visual-review.md), [receipt](../iterations/2026-03-23-ww11-layout-containers/evidence/cloud-verification.json) |

The official WW08 URL reuses `wow2025w9tab`; its title and WordPress REST post 21377 identify 2026 week 8. Folder dates remain the article dates. Author files and extracted inputs are SHA-256 locked in each `inputs/source-lock.json`; final published workbook, PNG and CSV hashes are in each Cloud receipt. Current case metadata is authoritative.

## Author and replica images

All images below are final REST exports. All five cases have independently reviewed Cloud images and accepted documented visual differences.

| Case / REST state | Author | SDK replica |
| --- | --- | --- |
| WW49 default Oklahoma | ![WW49 author](../iterations/2019-12-08-ww49-swap-states/outputs/cloud-author.png) | ![WW49 replica](../iterations/2019-12-08-ww49-swap-states/outputs/cloud-replica.png) |
| WW50 default 26 weeks | ![WW50 author](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-author.png) | ![WW50 replica](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-replica.png) |
| WW50 10 weeks | ![WW50 10 author](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-author-period-ten.png) | ![WW50 10 replica](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-replica-period-ten.png) |
| WW50 18 weeks | ![WW50 18 author](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-author-period-eighteen.png) | ![WW50 18 replica](../iterations/2019-12-15-ww50-retention-heatmap/outputs/cloud-replica-period-eighteen.png) |
| WW51 default | ![WW51 author](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-author.png) | ![WW51 replica](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-replica.png) |
| WW51 2019 | ![WW51 2019 author](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-author-year-2019.png) | ![WW51 2019 replica](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-replica-year-2019.png) |
| WW51 California | ![WW51 California author](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-author-california.png) | ![WW51 California replica](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-replica-california.png) |
| WW51 2019 / California | ![WW51 combined author](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-author-year-2019-california.png) | ![WW51 combined replica](../iterations/2019-12-23-ww51-sales-performance-dashboard/outputs/cloud-replica-year-2019-california.png) |
| WW08 default | ![WW08 author](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-author.png) | ![WW08 replica](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-replica.png) |
| WW08 California | ![WW08 California author](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-author-california.png) | ![WW08 California replica](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-replica-california.png) |
| WW08 Texas | ![WW08 Texas author](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-author-texas.png) | ![WW08 Texas replica](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-replica-texas.png) |
| WW08 California / Aaron Hawkins | ![WW08 Aaron author](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-author-california-aaron.png) | ![WW08 Aaron replica](../iterations/2026-03-01-ww08-dzv-filter-actions/outputs/cloud-replica-california-aaron.png) |
| WW11 default | ![WW11 author](../iterations/2026-03-23-ww11-layout-containers/outputs/cloud-author.png) | ![WW11 replica](../iterations/2026-03-23-ww11-layout-containers/outputs/cloud-replica.png) |

## Actual CSV scope and independent numerical evidence

Dashboard exports do not automatically include every sheet. The scope below follows actual columns/rows and independently queried data, rather than the export filename. In particular a headline/button CSV cannot prove an entire matrix.

| Case | Actual author CSV coverage | Actual replica CSV coverage | Independent checks and limits |
| --- | --- | --- | --- |
| WW49 | Selected State: seven city rows plus Oklahoma polygon aggregate. Diagnostic CHK:Data: IN Oklahoma and 25 OUT states. | Selected State city/polygon values and coordinates; States: all 25 OUT states, Sales, Global Rank and trellis positions. | City Sales and coordinates, nationwide/partition ranks and the complete default trellis match Hyper. All 49 single-state selections are calculated independently; alternate selection events were not executed. [Comparison](../iterations/2019-12-08-ww49-swap-states/evidence/cloud-data-comparison.json). |
| WW50 | Dashboard headline only; Data diagnostic: 1,431 cohort/week pairs with four measures; BAN:Data underlying headline measures. | Heat Map complete visible matrix, Bar complete marginal histogram and BAN headline. | Final hash-bound exports check all 675/387/595 visible matrix cells and all 27/43/35 marginal bars at periods 26/10/18, against the source diagnostic and independent Hyper. Headline denominators deduplicate cohort sizes; the row-repeated candidate is rejected. Independent oracle covers all 17 legal periods (10-26). [Comparison](../iterations/2019-12-15-ww50-retention-heatmap/evidence/cloud-data-comparison.json). |
| WW51 | Available dashboard exports cover Bar by Sub Cat, including files requested for weekly/monthly/matrix comparisons. These repeated exports do not cover those other author charts. | Dashboard plus standalone weekly, monthly and subcategory-month dot-matrix CSVs. | Final strict checks cover all 32 CSV file hashes, complete row/key sets and values in default, 2019, California and 2019 + California. Raw replica data match Hyper within 0.000001; author dollar-rounded labels allow 0.500001. Map/year-selector use independent Hyper plus PNG and artifact contracts. [Comparison](../iterations/2019-12-23-ww51-sales-performance-dashboard/evidence/cloud-data-comparison.json). |
| WW08 | Customer Orders Product Name / Measure Names / Measure Values: Sales and Quantity for all four states, even the hidden default panel. | Same complete product/measure pairs. | Both roles match independent Hyper per product and measure. CSV does not prove Profit Ratio, map geometry or customer domain. Main/customer aggregates are independently calculated; visibility/actions are artifact contracts. [Comparison](../iterations/2026-03-01-ww08-dzv-filter-actions/evidence/cloud-data-comparison.json). |
| WW11 | One Profit % Increase value. | Eight aggregate KPI columns: Profit/ratio changes plus CY/PY Sales, Profit and summed monthly Profit Ratio. | Actual exported values match Hyper at display precision. Monthly curves and 17-point scatter use separate Hyper/XML/PNG evidence, not dashboard CSV. [Comparison](../iterations/2026-03-23-ww11-layout-containers/evidence/cloud-data-comparison.json). |

In WW08's Aaron state the REST Customer Name filter applies globally to both author and replica, including Main KPIs and map. This capture does not establish browser quick-filter targeting; the generated shared customer-filter group targets Customer Orders and KPIs-Customer. In WW51, REST year/state filters establish data states rather than execution of the year-selection or hover-highlight actions.

WW11's ratio KPI intentionally follows the author's sum of monthly profit ratios: 154.8% CY versus 161.2% PY, with -6.4 percentage-point change. It is not the annual profit/sales ratio. The author's Total Profit CY/PY ratio-card captions are preserved.

## Reviewed differences and SDK feedback

WW49 matches the Oklahoma silhouette, seven cities and $19,683 rounded total, together with the complete ordered 5 x 5 trellis. Accepted differences are selected-map size/margins and label spacing/weight. Initial blank maps and a later blank trellis were rejected and fixed before final acceptance; preserved receipts document those attempts. Generic explicit geocoding context, binary exclusions, table-calculation partition preservation and set-action selection options resolved the case-driven gaps.

WW08 matches default hidden panel and California/Texas/customer-visible states, KPI values/order, state titles and Reset rectangle. Accepted differences are map boundaries/viewport, table/control typography and cell formatting; in the narrow Aaron table Quantity appears as Quanti..., with correct data. Generic dynamic-zone visibility graphs, parameter text runs, relevant filter domains and linking selected worksheet filters support the case through public APIs.

WW11 matches the nested container arrangement, readable three-card KPIs, change badges, current/prior trends and quadrant scatter. Accepted differences are solid prior-year lines without source dots, plot frames, mark outlines/sizes and footer typography. Generic rounded container corners and support for field-rich labels/custom palette contexts preserve the design without source-template construction.

WW50 matches all three parameterized retention matrices, Viridis legend, marginal histogram and headlines 21.2% / 23.5% / 21.3% at 26/10/18 weeks. Accepted differences are modest padding/font weight, a visible Time Period caption and footer hyperlink decoration. Long September cohort dates are truncated in both author and replica at 10 weeks; the author saved selection tint is not reproduced. The actual CSV denominator diagnosis and every visible matrix/marginal row are verified independently.

WW51 matches all six views in four data states, including Sunday weekly peaks, monthly sales patterns, subcategory ordering, sparse matrix holes and California silhouette. The earlier Sunday-versus-Monday boundary was diagnosed using the author Cloud area-curve edge and independently aggregated Hyper weekly vectors, then corrected before acceptance. Sunday/Monday fitted curve mean-square errors (pixels squared) were 4.56/78.71 for default, 0.59/101.44 for 2019, 8.21/110.33 for California and 1.11/226.24 for the combined state; all four support Sunday. [Quantified diagnosis](../iterations/2019-12-23-ww51-sales-performance-dashboard/evidence/weekly-boundary-image-diagnosis.json). Accepted differences are absent brown dot-row/year-selector baseline guides, omitted dollar prefixes on rounded sales labels, and modest title/footer/padding/map-margin differences. Year filtering and bottom-three-sheet hover-highlight definitions are verified through artifact contracts; REST filters do not prove browser execution. The generic enhancement details and synthetic regression contracts are maintained in [cwtwb case-driven enhancements](https://github.com/aidatacooper/cwtwb/blob/main/docs/case-driven-enhancements.md).

## Validation and reproducibility

- Verified SDK version: 0.27.1. Exact final validated SDK commit: **[f0e385b2f1abe845536e17041f2c2aaeb3c11fba](https://github.com/aidatacooper/cwtwb/commit/f0e385b2f1abe845536e17041f2c2aaeb3c11fba)**.
- SDK regression result: **507 passed, 25 skipped**.
- Case shared-suite result: **55 passed**.
- Final repository validation: all **30 active cases** passed metadata, source-lock and catalogue checks; all **30** passed isolated build/verifier checks using the remote pinned SDK.
- SDK CI: [successful run 37030838191](https://github.com/aidatacooper/cwtwb/actions/runs/37030838191), 507 passed / 25 skipped. Case CI is checked after push by the coordinating maintainer; [workflow history](https://github.com/aidatacooper/wow-tableau-problem-solving/actions/workflows/validate-case.yml).
- Case repository: [main commit history](https://github.com/aidatacooper/wow-tableau-problem-solving/commits/main/); the final commit SHA is reported in the maintainer completion message.

The SDK and shared-suite results above are measured against the remote pinned SDK, installed without editable mode. All isolated rebuilds used disposable copies, preserving the reviewed final Cloud workbook bytes and hashes. Each real execution is recorded in schema-1.1 cwtwb.runs; editable-development results are identified as such rather than presented as a released baseline.

Install Python 3.11 dependencies from requirements.txt. For a new artifact, run `python scripts/validate_iteration.py iterations/<case>` and the shared unittest suite. For already captured final artifacts, run the case verifier directly, its cloud-data comparer where available, and `validate_iteration.py --metadata-only`. A rebuild changes workbook identity/hash and requires a new publish/export/review cycle; do not invalidate final evidence by casually rebuilding in place. Cloud credentials belong only in process environment variables and are absent from committed evidence.


Each case includes a non-secret `evidence/cloud-request.json` with repository-relative paths. To repeat Cloud capture, first restore the author reference workbook at its declared path from the recorded public source, then run `python scripts/capture_case_cloud.py iterations/<case>/evidence/cloud-request.json` from the repository root with Cloud credentials in the process environment. The author reference is not needed to rebuild the replica from its locked inputs. A new capture requires a fresh independent review before its status is accepted.
