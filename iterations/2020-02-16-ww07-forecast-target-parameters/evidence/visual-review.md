# Cloud review: 2020 WW07

Decision: `replicated / acceptable_delta` within Cloud REST parameter-state, independent data and artifact-contract scope. Pixel matching is not claimed.

Reviewed artifact SHA-256: `16f90f16fec16ee21918f90a33244353b4d6a97fe4acd35111961ed49ec145ea`.

All twelve paired PNGs across six REST states were inspected and compared with the previously accepted baseline. The blue actual bars now have approximately the author thickness, teal forecasts remain visible as thinner overlays, and black target ticks span the row. Full-height gray side panels restore the input/selector/reset partitions. Forecast and target circles are large and legible; target circles correctly change from hollow to filled for selected categories. Native vertical flow fixes the first polish attempt's stretched selector layout, and both reset glyphs now render at the large readable size. Each category remains associated with its bar and separate label row; no clipping, label overlap or obscured parameter/reset control was observed.

Technology +70,000 extends the teal forecast; Furniture -25,000 shortens it. Custom targets move the corresponding ticks and fill the target selector circles. Combined applies both forecasts and target changes. Reset matches default. The chart/selector colors and each displayed target, YTD sales, forecast and signed percentage agree with the original across the six reviewed states.

| State | Author | Replica |
| --- | --- | --- |
| default | [image](../outputs/cloud-author.png) | [image](../outputs/cloud-replica.png) |
| technology-forecast | [image](../outputs/cloud-author-technology-forecast.png) | [image](../outputs/cloud-replica-technology-forecast.png) |
| negative-forecast | [image](../outputs/cloud-author-negative-forecast.png) | [image](../outputs/cloud-replica-negative-forecast.png) |
| custom-target | [image](../outputs/cloud-author-custom-target.png) | [image](../outputs/cloud-replica-custom-target.png) |
| combined | [image](../outputs/cloud-author-combined.png) | [image](../outputs/cloud-replica-combined.png) |
| reset | [image](../outputs/cloud-author-reset.png) | [image](../outputs/cloud-replica-reset.png) |

Independent verification queries all3,312 locked2019 facts, aggregates three categories, and applies forecast/target tokens without reading workbook calculations. All24 chart/label CSV files pass:18 numeric exports each cover three categories with five metrics (270 metric cells); six replica label exports additionally verify currency values and six signed percentage strings per state. Null forecasts remain blank. Whole-dollar and whole-percent display rounding is respected. Selector/reset-button CSVs do not establish bar-data correctness.

Remaining differences: the chart is narrower because labels occupy a fixed right-hand column, the numeric x-axis is hidden, and bar/selector centers differ by a few pixels within each category row. Selector row spacing and reset placement differ slightly from the author. Subtitle styling is regular rather than italic, forecast differences omit surrounding parentheses, and lighter footer/link typography uses SDK attribution. These presentation differences do not alter category association, bar-length ratios, targets or readable values.

Parameter selection/reset events, source/target worksheets, clear-selection behavior and self-deselection actions are checked in the generated artifact. Independent token-sequence checks cover replacement and reset. REST states supply parameter values directly; no browser click or hover was executed. The original comparison package only exposes hidden worksheet windows and is never read by the builder. Earlier accepted baseline and rejected first-polish layouts are retained in ignored scratch; current workbook/image/CSV hashes bind the accepted evidence. The artifact is frozen.

The final SDK correction places the floating vertical-flow side panels directly under dashboard zones, matching their native coordinates. This final artifact was reviewed again across all twelve author/replica PNGs and all twenty-four chart/label CSVs. The panel positions now follow the source margins; the title and subtitle have an explicit gap beyond the left panel and their first characters are completely visible in every state. Both reset glyphs, all selectors, input values and separate metric labels remain readable without overlap. The rejected intermediate title occlusion is archived in `scratch/polish-nativeflow-title-failed-ww07`; the accepted pre-SDK comparison remains in `scratch/polish-pre-nativeflow-ww07`. No actual browser events were executed. The final artifact is frozen.
