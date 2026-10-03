# Cloud visual review — WW03

Result: `acceptable_delta`. The author comparison and independent replica were reviewed in both Cloud REST states: `Time Selector=Weeks` (displayed as Weekdays) and `Time Selector=Days`. This is a rendered-image and data-state review; no browser clicks or hovers were executed. It is not a pixel-equality claim.

| REST state | Author | Replica |
| --- | --- | --- |
| Weekdays / Weeks | [Image](../outputs/cloud-author.png) | [Image](../outputs/cloud-replica.png) |
| Days | [Image](../outputs/cloud-author-days.png) | [Image](../outputs/cloud-replica-days.png) |

Both states reproduce the three-month columns and four-quarter rows, reversed Hours axes, orange circles with size/colour driven by distinct orders, grey min/max hour ranges, and dotted linear trends. The Weekdays view runs Sunday through Saturday with horizontal abbreviated labels. The selected radio control and subtitle reflect the REST parameter value. The Days state replaces the weekday plot with day-of-month positions. No unwanted empty worksheet occupies half the dashboard.

The final sizing uses the source's separate daily and weekday mark sizes. Remaining differences are small plot padding and tick placement, lighter/thinner trendline appearance, and the footer: the replica identifies cwtwb and has a plain challenge URL, while the reference identifies Donna Coles and also includes a data attribution. The author's Days capture contains a saved blue Q3 axis selection; the replica's corresponding axis is unselected. That saved author selection is not treated as a browser interaction test.

The independent verifier checks the complete active worksheet exports from both workbooks, not the dashboard or a header/button export. Each Weekdays export contains 1,047 circle marks and 82 Gantt spans; each Days export contains 1,495 circles and 322 spans. Every month/day-or-weekday/hour distinct-order count, quarter/month-column coordinate, maximum hour and negative range matches the locked Hyper oracle. Circle counts sum to all 1,687 latest-year orders. The opposite sheet is empty in each state. See [Cloud data comparison](cloud-data-comparison.json) and [independent oracle](functional-verification.json).

The original reference package is kept outside the iteration. Its analysis-only comparison copy removes `hidden=true` from worksheet window metadata so REST can export both complete sheets. It retains source calculations, data, actions and dashboard layout and is never read by the replica builder. [Export provenance](export-provenance.json) binds the original and comparison hashes; [Cloud evidence](cloud-verification.json) binds published source and final replica hashes plus all rendered files. The verifier rejects stale workbook bindings and empty active-state exports.
