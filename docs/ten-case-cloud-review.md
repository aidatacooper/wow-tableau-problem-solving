# Ten-case Cloud review

Each replica is generated from an empty workbook through public cwtwb APIs. Images below are actual Tableau Cloud exports. Current screenshots/CSVs and historical run records are committed; repeated intermediate PNG/CSV exports remain on the validation server. Author sources remain separate; historical source locks are retained as provenance. The two date identities are article publication date and official challenge date.

CSV comparisons establish only their documented exported scope. Static images, parameterized REST exports, and XML definitions do not establish browser hover or click behavior. Current acceptance and outstanding work are authoritative in each case.yaml and evidence/visual-review.json.

| Case | Author Cloud | SDK replica Cloud |
| --- | --- | --- |
| 2019-07-18-ww29-high-orders | ![Author](../iterations/2019-07-18-ww29-high-orders/outputs/cloud-author.png) | ![Replica](../iterations/2019-07-18-ww29-high-orders/outputs/cloud-replica.png) |
| 2019-07-25-ww30-navigation-kpi | ![Author](../iterations/2019-07-25-ww30-navigation-kpi/outputs/cloud-author.png) | ![Replica](../iterations/2019-07-25-ww30-navigation-kpi/outputs/cloud-replica.png) |
| 2019-08-04-ww31-hub-spoke-map | ![Author](../iterations/2019-08-04-ww31-hub-spoke-map/outputs/cloud-author.png) | ![Replica](../iterations/2019-08-04-ww31-hub-spoke-map/outputs/cloud-replica.png) |
| 2019-08-09-ww32-step-area-chart | ![Author](../iterations/2019-08-09-ww32-step-area-chart/outputs/cloud-author.png) | ![Replica](../iterations/2019-08-09-ww32-step-area-chart/outputs/cloud-replica.png) |
| 2019-08-14-ww33-table-formatting | ![Author](../iterations/2019-08-14-ww33-table-formatting/outputs/cloud-author.png) | ![Replica](../iterations/2019-08-14-ww33-table-formatting/outputs/cloud-replica.png) |
| 2019-09-02-ww34-top-n-single-worksheet | ![Author](../iterations/2019-09-02-ww34-top-n-single-worksheet/outputs/cloud-author.png) | ![Replica](../iterations/2019-09-02-ww34-top-n-single-worksheet/outputs/cloud-replica.png) |
| 2019-09-09-ww36-custom-axis-tracker | ![Author](../iterations/2019-09-09-ww36-custom-axis-tracker/outputs/cloud-author.png) | ![Replica](../iterations/2019-09-09-ww36-custom-axis-tracker/outputs/cloud-replica.png) |
| 2026-02-02-ww04-dynamic-moving-average | ![Author](../iterations/2026-02-02-ww04-dynamic-moving-average/outputs/cloud-author.png) | ![Replica](../iterations/2026-02-02-ww04-dynamic-moving-average/outputs/cloud-replica.png) |
| 2026-02-09-ww05-kpi-period-comparison | ![Author](../iterations/2026-02-09-ww05-kpi-period-comparison/outputs/cloud-author.png) | ![Replica](../iterations/2026-02-09-ww05-kpi-period-comparison/outputs/cloud-replica.png) |
| 2026-02-15-ww06-null-safe-averages | ![Author](../iterations/2026-02-15-ww06-null-safe-averages/outputs/cloud-author.png) | ![Replica](../iterations/2026-02-15-ww06-null-safe-averages/outputs/cloud-replica.png) |

## SDK changes and case origins

- WW32: retain the full nested table-calculation context in datasource color palette bindings so Cloud renders increase/decrease/baseline colors correctly.
- WW33: distinguish column dual-axis classes and pane-scoped cell formats, preserving outlined background marks and separate bar labels.
- WW34: independent nested calculation addressing and ordering, including regional Top N rank and Other aggregation.
- WW31: legacy layered-map coordinate folds and quoted region color palette keys; map style and regional layer rendering.
- WW06: Sunday week options, real average subtotals, table subtotal field references, pane formatting and mapped filter actions.
- WW30: real and calculated field default formats plus floating navigation buttons at the dashboard level.
- WW04: parameter-driven axis titles and correctly scoped synchronized axes.
- WW05: rich dynamic parameter titles and horizontal color legend support.

Public interfaces, tests and exact behavior are documented in cwtwb/docs/case-driven-enhancements.md. Case requirements pin the reviewed SDK Git commit rather than depending on an unreleased PyPI version.

## Reproduce

Install requirements.txt, then run python scripts/validate_iteration.py iterations/<case>. This builds and verifies a fresh artifact. Publishing requires TABLEAU_SERVER_URL, TABLEAU_SITE_ID, TABLEAU_TOKEN_NAME and TABLEAU_TOKEN_SECRET in the process environment, then python scripts/publish_to_cloud.py <twbx> --name <review-name> --project default. Do not store the secret in the repository.

After final Cloud captures, run the verifier directly or validate_iteration.py --metadata-only: a rebuild generates fresh workbook identities and requires a new capture. Each case verify_cloud_data.py compares saved exports without accessing credentials. Browser action verification requires an authenticated Tableau web session; PAT authentication for REST is separate.

## Current acceptance

All ten cases pass local artifact contracts and have actual author/replica Cloud image reviews with acceptable visual differences. Five have completed the reported functional/state checks; five retain explicit browser interaction work. No case is marked pixel-identical.

| Case | Functional | Visual | Remaining acceptance |
| --- | --- | --- | --- |
| 2019-07-18-ww29-high-orders | replicated | acceptable_delta |  |
| 2019-07-25-ww30-navigation-kpi | partial | acceptable_delta | Authenticated browser verification: click each KPI into its correct detail dashboard, then GO BACK. Static render and UUID correctness do not prove actual click execution. |
| 2019-08-04-ww31-hub-spoke-map | partial | acceptable_delta | Finish current Cloud state and visual review; browser actions require real hover/click evidence. |
| 2019-08-09-ww32-step-area-chart | replicated | acceptable_delta |  |
| 2019-08-14-ww33-table-formatting | replicated | acceptable_delta |  |
| 2019-09-02-ww34-top-n-single-worksheet | partial | acceptable_delta | Real browser hover must highlight corresponding manufacturer rank across regions and restore on leaving; three REST parameter states and all CSV values already agree. |
| 2019-09-09-ww36-custom-axis-tracker | partial | acceptable_delta | Real browser hover must update the tracking reference line; static image and CSV do not verify action execution. |
| 2026-02-02-ww04-dynamic-moving-average | replicated | acceptable_delta |  |
| 2026-02-09-ww05-kpi-period-comparison | replicated | acceptable_delta |  |
| 2026-02-15-ww06-null-safe-averages | partial | acceptable_delta | Finish current Cloud state and visual review; browser actions require real hover/click evidence. |
