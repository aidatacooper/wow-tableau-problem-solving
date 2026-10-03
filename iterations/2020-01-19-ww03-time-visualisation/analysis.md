# WW03 — Orders by time and day

The [19 January 2020 article](https://donnacoles.home.blog/2020/01/19/can-you-visualise-time-in-a-unique-way/) recreates Lorna Eden's [2020 WW03 challenge](https://www.workout-wednesday.com/2020w03/). The business question is when additional staff should support order processing. The author joins Superstore order lines to order times and shows a twelve-month, three-column/four-quarter display. Days and Weekdays offer different staffing perspectives.

Only the packaged joined Hyper is a build input. The author workbook was inspected during analysis and is never read by the builder. Its lock records the original package and the independently extracted data hash. The builder starts with `TWBEditor("")` and public SDK APIs.

The source has 9,994 order lines covering 2016–2019. The latest year is 2019, with 3,312 lines and 1,687 distinct orders. Multiple lines for one order must not inflate circle size or colour. The hour is the integer before the first colon in `Time of Order`. Each circle counts distinct order IDs within month, day/weekday, and hour. Grey Gantt ranges cover the earliest through latest order hour for the day or month/weekday group. Weekday groups include year in their LOD, avoiding cross-year mixing.

The independently recomputed latest-year oracle covers all twelve months: 1,495 day/hour circles and 322 daily spans; 1,047 weekday/hour circles and 82 month/weekday spans. Missing combinations are absent rather than fabricated zero orders. The month-column expression cycles 1, 2, 3; quarter provides the four rows. Reversed hour axes put earlier hours above later hours, with five-hour ticks and synchronised circles/ranges.

The two original worksheets are `By Day` and `By Weekday`. The parameter `Time Selector` accepts `Days` and `Weeks`; `Weeks` displays the alias `Weekdays`. Complementary boolean filters select the relevant sheet. A vertical dashboard container performs sheet swapping. The SDK-native linear trendline requires a reusable pane specification; a synthetic regression in the SDK covers that primitive independently of this case.

The baseline SDK 0.27.1 at `f0e385b2f1abe845536e17041f2c2aaeb3c11fba` silently ignored a pane trendline specification. A separate process loaded those exact sources and built a synthetic X/Y circle chart with zero native trendline elements; `evidence/sdk-baseline.json` records the result. The final build uses the generic native trendline API. Its latest-year filter uses the explicit `{FIXED: MAX(YEAR([Order Date]))}` scalar LOD, ensuring a row-level comparison. The independently verified generated column instance must have derivation `None`.

Acceptance checks:

- Locked joined Hyper remains byte-identical inside the generated TWBX.
- Both worksheets filter dynamically to the latest year and use complementary selector values.
- Every circle uses distinct orders for colour and size; native Gantt marks use a negative min/max range.
- Month and quarter form the twelve-month display; hour axes reverse, synchronise and use five-hour ticks.
- Both selector states publish and render through Cloud REST; complete worksheet CSVs are compared to every independent circle count and span.
- Linear dotted trends remain native worksheet artifacts. No browser parameter click, hover or tooltip execution is claimed.

Cloud exports identify circle and Gantt coverage separately. Dashboard/header CSVs are insufficient to prove the underlying matrices. Visual differences and the exact export scope are recorded after the final Cloud comparison; `acceptable_delta` does not mean pixel equality.
