# Cloud review: 2020 WW07

Decision: `replicated / acceptable_delta` within Cloud REST parameter-state, independent data and artifact-contract scope. This is not a pixel-identical reproduction.

Reviewed artifact SHA-256: `4ab5812bb26e984c560c2a5108706bc5145b1347514f36db6fbccb6b031aeed7`.

All six paired 2000 ? 1000 REST images were inspected. Sales remain blue, forecast is a thinner teal overlay, and targets are black ticks. Category selectors, chart and separate label rows align. No duplicate or overlapping measure labels remain. Technology +70,000 extends the forecast; Furniture ?25,000 shortens it; custom targets move the corresponding ticks; the combined state applies both changes; reset matches default.

| State | Author | Replica |
| --- | --- | --- |
| default | [image](../outputs/cloud-author.png) | [image](../outputs/cloud-replica.png) |
| technology-forecast | [image](../outputs/cloud-author-technology-forecast.png) | [image](../outputs/cloud-replica-technology-forecast.png) |
| negative-forecast | [image](../outputs/cloud-author-negative-forecast.png) | [image](../outputs/cloud-replica-negative-forecast.png) |
| custom-target | [image](../outputs/cloud-author-custom-target.png) | [image](../outputs/cloud-replica-custom-target.png) |
| combined | [image](../outputs/cloud-author-combined.png) | [image](../outputs/cloud-replica-combined.png) |
| reset | [image](../outputs/cloud-author-reset.png) | [image](../outputs/cloud-replica-reset.png) |

The independent verifier queries all 3,312 locked 2019 facts, aggregates three categories and applies forecast/target tokens independently of workbook calculations. All 24 exported chart/label CSV files pass: 18 numeric exports each cover three categories ? five metrics (270 metric cells), and six replica label exports additionally verify currency values and six signed percentage strings per state. Null forecast values remain blank. Currency comparisons respect whole-dollar display rounding; percentages respect whole-percent display rounding. Selector and reset-button CSVs do not establish bar-data correctness.

Remaining visual differences: actual bars and target ticks are thinner; selector dots and reset glyphs are smaller; unselected target circles render filled rather than hollow. Gray panels occupy the category row band rather than extending the author?s full dashboard height. The replica places labels in a fixed right-hand column, hides the numeric x-axis and replaces the author subtitle/attribution typography with a simpler title/footer. These affect presentation, while category order, color meaning, forecast direction, targets and displayed values agree across the reviewed states.

Selection and reset events, source/target worksheets, parameter targets and clear-selection behavior are checked in the generated workbook contract. Token replacement and reset logic are independently exercised. REST states are supplied directly; no browser clicks or hovers were executed. The author comparison package only exposes originally hidden worksheet windows for REST export and is never read by the builder.

The SDK baseline identified breakdown-off, virtual Measure Names color and virtual Measure Names size gaps; generic SDK fixes and synthetic regression coverage are recorded in `sdk-baseline.json` and the SDK enhancement documentation.
