# Cloud REST review: 2019 WW51

Accepted as `replicated / acceptable_delta` under Cloud REST images, data states and generated-workbook contracts. Actual author and replica PNGs were inspected side by side for default, 2019, California, and 2019 + California. This is not a pixel-identical reproduction.

| State | Author image | Replica image | Independent sales total |
| --- | --- | --- | ---: |
| Default | [Author](../outputs/cloud-author.png) | [Replica](../outputs/cloud-replica.png) | 2,297,200.8603 |
| 2019 | [Author](../outputs/cloud-author-year-2019.png) | [Replica](../outputs/cloud-replica-year-2019.png) | 733,215.2552 |
| California | [Author](../outputs/cloud-author-california.png) | [Replica](../outputs/cloud-replica-california.png) | 457,687.6315 |
| 2019 + California | [Author](../outputs/cloud-author-year-2019-california.png) | [Replica](../outputs/cloud-replica-year-2019-california.png) | 146,388.3445 |

All six views render in every state. Sunday weekly peaks match the author's sequence, monthly bar patterns and colors match, subcategory order and marginal values align, sparse matrix holes and colored circles match, and California filters show the California silhouette. Year selection is reflected in the visible year mark and 12-month matrix. The brown gradient and floating chart arrangement preserve the intended dashboard design.

Remaining differences are visible and accepted: source brown horizontal guide lines across the dot rows and the year-selector baseline are absent; replica sales labels omit the dollar prefix but retain the same rounded values; title weight, footer placement/link appearance, chart padding and map margins differ modestly. Year-circle sizing is close after adjustment. These do not change the sales values, matrix coverage or filter-state interpretation.

`verify_cloud_data.py` verifies the current workbook SHA256, exact four-state coverage, all 32 CSV file hashes, complete row/key sets and all values. Every author export is **Bar by Sub Cat only**, including exports paired with replica weekly/monthly/matrix views. Author labels are dollar-rounded, accepted within 0.500001; replica independent weekly, monthly, entire populated subcategory-month matrix and marginal-bar values match the raw Hyper oracle within 0.000001. The author dashboard CSV is not evidence for its entire matrix. State-map and year-selector data are reconciled independently in Hyper and inspected in the PNGs; no separate complete author map or matrix CSV is available.

The Sunday-versus-Monday image diagnosis is retained in [weekly-boundary-image-diagnosis.json](weekly-boundary-image-diagnosis.json), and all detailed value checks are in [cloud-data-comparison.json](cloud-data-comparison.json). Captured hashes and REST filter states are in [cloud-verification.json](cloud-verification.json).

No browser click or hover was executed. Year select filtering, bottom-three-sheet hover highlighting, their source/target exclusions and clear behavior are verified from generated-workbook contracts. REST year/state filtering verifies data states rather than action event execution.
