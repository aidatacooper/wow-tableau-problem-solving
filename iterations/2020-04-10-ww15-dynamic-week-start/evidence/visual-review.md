# Cloud visual and data review ? 2020 WW15

Accepted within the documented scope as `acceptable_delta`. Reviewed artifact SHA256: `00198e0b4ce64301b34abac4b585be9b5c27b0dba19ccc545928c85de823fea3`. The complete independent verifier passes with released SDK `56377c5b170f0df1f5cd853fc483de26962dfed1`.

All eight paired REST images were inspected. The titles now render the correct weekday start and end, selected ending date and number of prior weeks. They no longer show missing or ?None? values. Both top-right parameter cards remain visible. The latest week is teal in front of the gray prior weeks, all seven weekday positions are readable, and the sales axis uses the original fixed range.

| REST state | Ending date / prior weeks | Paired images | Author / replica daily cells |
| --- | --- | --- | --- |
| Default: Friday?Thursday | 2019-10-24 / 10 | [Author](../outputs/cloud-author.png), [replica](../outputs/cloud-replica.png) | 77 / 77 |
| Sunday ending: Monday?Sunday | 2019-10-27 / 4 | [Author](../outputs/cloud-author-sunday.png), [replica](../outputs/cloud-replica-sunday.png) | 35 / 35 |
| Monday ending: Tuesday?Monday | 2019-10-28 / 1 | [Author](../outputs/cloud-author-monday.png), [replica](../outputs/cloud-replica-monday.png) | 14 / 14 |
| Current week only: Friday?Thursday | 2019-10-24 / 0 | [Author](../outputs/cloud-author-current-only.png), [replica](../outputs/cloud-replica-current-only.png) | 6 / 7 |

The [CSV comparison](cloud-data-comparison.json) validates every exported week/day cell against daily aggregates independently calculated from the original locked 9,994-row Hyper. All eight full Viz CSVs pass: 132 author cells and 133 replica cells, 265 total. No title, parameter-card or button CSV is used to prove the chart. The [functional verifier](functional-verification.json) also checks the derived 1,461-day calendar CSV and Hyper against every original daily sales value and the unchanged sales total of 2,297,200.8603.

The current-only author view omits its first day, Friday 2019-10-18, because that zero-fact date precedes its native date-domain minimum. The replica deliberately includes this day with zero sales and validates all seven days. This is the sole narrowly declared source-data exception; both other zero-fact Fridays in the Monday-ending state are present, and all other source and replica grids are complete. The source current-only image therefore starts at Saturday while the replica starts at Friday.

Remaining visual differences are slightly lighter title/axis typography, modest plot and footer padding differences, and centered attribution text in place of the source's edge-aligned columns. Attribution identifies CWTWB as the reconstruction tool. No values, controls, weekday headings or title context are clipped. The extra leading zero day in the current-only state is an intentional completeness correction. The result is not pixel-identical.

The title weekday fields are actual detail/LOD encodings, and the date-range completion and conditional no-sales tooltip text are checked as workbook contracts. Cloud CSVs cover sales and available tooltip dates. No browser hover or click was executed, so the review does not claim a rendered hover tooltip or event execution. The author export changes only hidden worksheet-window flags; [export provenance](export-provenance.json) records the transformation.
