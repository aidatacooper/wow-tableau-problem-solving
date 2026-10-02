# Cloud REST visual and numerical review

Result: replicated / acceptable_delta. The final published workbooks and all four author/replica image pairs were inspected side by side. Identity and exported-file hashes are recorded in cloud-verification.json. No browser click, hover, or action execution is claimed.

| REST state | Author image | Replica image | Reviewed result |
| --- | --- | --- | --- |
| Default | [author](../outputs/cloud-author.png) | [replica](../outputs/cloud-replica.png) | Customer panel hidden; KPI values $2297.2K, $286.4K, 12.5%, 37873 match. |
| California | [author](../outputs/cloud-author-california.png) | [replica](../outputs/cloud-replica-california.png) | Panel visible, title California; $457.7K, $76.4K, 16.7%, 7667 match. |
| Texas | [author](../outputs/cloud-author-texas.png) | [replica](../outputs/cloud-replica-texas.png) | Panel visible, title Texas; $170.2K, -$25.7K, -15.1%, 3724 match. |
| California + Aaron Hawkins | [author](../outputs/cloud-author-california-aaron.png) | [replica](../outputs/cloud-replica-california-aaron.png) | Five product rows and customer KPIs $1.3K, $0.2K, 13.5%, 23 match. |

In the Aaron state, the REST Customer Name filter applies globally to both author and replica, including Main KPIs and the map. This capture does not demonstrate browser quick-filter targeting. The generated artifact independently binds the related customer filter to Customer Orders and KPIs-Customer; action event, source, target and clear contracts, reset parameter and dynamic visibility graph are checked by verify_replication.py.

verify_cloud_data.py --strict-workbook passed on the final workbook. Actual dashboard CSV exports cover Customer Orders Product Name / Measure Names / Measure Values for Sales and Quantity, including the hidden default panel. All exported product/measure pairs for both roles and four states match an independent locked-Hyper aggregation. These CSVs do not cover Profit Ratio, map geometry, or the customer domain. Those claims are limited to Hyper calculations, artifact checks and the rendered image states.

Accepted visual differences: the replica map retains extra geographic boundaries and a different viewport; customer controls and table typography differ slightly in background, weight and spacing; Sales uses one decimal where some author states show integer cells. In the narrow customer-selected table the Quantity header is displayed as Quanti..., while its numeric values and the full-state table remain correct. Reset rectangle, KPI labels/order, state titles and panel visibility render correctly. This is not a pixel-identical result.
