# WW24 final paired Cloud review

Result: **acceptable_delta**, reviewed 2026-10-03. The result is not pixel-identical.

Replica artifact SHA256: `522910fd8eed51d10a2a5c0d9945b82aa7f9f38dc507739651e7f3fac3bfacd0`.
Author comparison artifact SHA256: `327ea11171e9a930e32866e86947ea2a250b91a21e91095055172a17a2ac163d`.
Cloud PNG and CSV hashes are bound to these workbooks in the capture manifest. No accepted workbook rebuild followed capture.

## Full image review

All eight PNGs were inspected: author and replica for default Davidson, three-day Davidson, Campbell and Los Angeles. All four metric columns (New Cases, Reported Cases, 3 Day Moving Avg and 14 Day Moving Avg) are visible in every replica viewport. Native fit-width eliminates the previous offscreen fourteen-day column. Source-native `n#,##0;-#,##0` formatting displays whole-number metrics, matching source presentation, without hash placeholders or excessive decimals. The actual formulas retain full precision; no ROUND calculation was added. Column headers are fully readable, with an additional explicit "along Report Date" description on the replica's moving-average headers.

| REST state | Latest trend in both renders | Map and series checks |
| --- | --- | --- |
| Default, Tennessee - Davidson, 14 days | 1 day INCREASE as of Sun, Jun 7 | Davidson red; fourteen-day curve and all daily outlined bars visible. First table row 124 new, 6,156 reported, 108 / 102 displayed averages. |
| Three-day Davidson | 1 day INCREASE as of Sun, Jun 7 | Same county/map/table, selector label changes to 3 Day Moving Avg and the line changes to the correct more variable three-day curve. |
| Tennessee - Campbell | 6 day DECREASE as of Sun, Jun 7 | Campbell green; small positive and negative daily bars and low moving-average curve; Campbell is first in the county table. |
| California - Los Angeles | 3 day INCREASE as of Sun, Jun 7 | California map with Los Angeles red; correct higher-scale daily series; first row 1,506 new, 63,844 reported, 1,398 / 1,347 displayed averages. |

The moving-average line uses the source red INCREASE and teal DECREASE palette in all four states. The bar width now reproduces individual daily marks instead of overlapping wide bars. Selected-county-first ordering followed by historical reported-case ordering matches the source's visible rows (including the source's non-monotonic latest-total ordering).

## Independent data coverage

The direct verifier independently recomputes all 422,143 locked raw rows: 3,037 county histories over 139 dates, including moving averages and recursive consecutive-direction days. Locked raw data and packaged Hyper hashes are identical. It then checks all 24 CSV exports against this oracle and validates every file/workbook hash. There are 15,704 numeric/direction comparisons, including extra available tooltip metrics; this comparison count includes repeated exported values, not that many distinct raw records.

The eight latest-table exports cover every county with all four metrics: 96 Tennessee county labels in each of its three states and 59 California county labels in the Los Angeles state, including the packaged Unknown label. The eight bar/line exports cover every one of the 92 dates from March 8 through June 7 for the selected county, requiring new cases and the selected moving average for every date. The eight BAN exports check latest-date trend direction and consecutive-day count.

The bar/line oracle applies the worksheet's physical March 8 filter before window calculations. Its first Davidson fourteen-day average is 1. Latest table/BAN calculations retain the complete January 21 onward histories before the late LOOKUP date filter. Default latest Davidson has full-precision averages 108.3333333333 and 101.7857142857. CSV comparisons respect each export's actual displayed decimal precision; rounded display exports do not prove arbitrary decimal precision. Full-precision formulas and the independent raw-data calculation provide that complementary evidence.

REST parameters establish the declared data/image states. Parameter domains, exact date grains, nested table-calculation dependencies, geographic roles, color encodings and native table viewport are artifact-verified. No browser typing, clicking, hovering or scrolling was executed or claimed; the full-table CSV covers rows outside the visible viewport.

## Remaining visual differences

The replica uses a darker map basemap with state labels rather than the source's faint neighboring county boundaries. Its legend entries are vertical rather than horizontal, and the latest-trend BAN is right aligned instead of left aligned. The title has a different left inset and omits the source's black underline. The table omits the source's County field heading; its moving-average headings include the complete "along Report Date" wording. Its lower viewport contains a partial next row, while the full CSV still covers every county. The March 8 reference-line/date annotation is omitted from the chart, whose start date remains exact in the data and filter contract. Date ticks use shorter month labels; footer text is dark rather than pink and attribution differs. These presentation differences are recorded explicitly. All required values, trend/color semantics, parameter states and four metric columns remain readable and independently verified.
