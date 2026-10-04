# WW37 Cloud review

Result: **acceptable_delta** within Cloud REST image/data states plus native artifact contracts. This is not a pixel match.

Replica TWBX SHA256: `35439de0c20e54eddf91efad1b67987cc3fd90143ca184ce1afbf71320fdadd4`.

All eight PNGs were inspected in author/replica pairs: default, California, June dates, and May-June dates. The filled continental-state map, black subscriber circles, readable title, custom subscriber legend, YoY legend, Date control, and source credits are present. All states remain visible in the three continental views; California is isolated in its filtered state. State colors follow the correct signed YoY data, subscriber-circle size ordering is preserved, and neither labels nor the map are obscured.

All **16 full worksheet CSVs**, covering both original and replica Map and Trend in all four states, passed the independent locked-Hyper oracle. Map contains two exported pane rows per state; both copies are checked, including exact CY/PY and formatted YoY/share precision. Trend checks the entire State/year/plotted-date key set and every subscription sum. There are 486,872 raw subscription records, aggregated to 26,609 State/date groups before filtering.

| REST state | States | Trend marks per workbook | CY | PY |
| --- | ---: | ---: | ---: | ---: |
| default | 48 | 2,592 | 185,341 | 165,191 |
| California | 1 | 54 | 19,528 | 17,600 |
| June dates | 48 | 384 | 22,134 | 15,197 |
| May-June dates | 48 | 672 | 44,323 | 29,651 |

**Date scope:** the two ISO-date equality lists are additional post-context filters. They preserve the native January 1-July 14 context, remain Weekly, and align plotted weeks to Wednesday. The replica diagnostic MIN/MAX columns confirm the unchanged bounds in every exported row. Partial plotted weeks in these subsets are expected because individual dates have been removed. These exports do **not** execute a daily-range switch or change the week-start day. Daily June and Monday-aligned May-June window behavior is independently calculated from raw records and the native filter/LOD/switching contracts are verified, but runtime range switching is outside the REST execution scope. Native Full Weeks only applies to Map and Trend, excluding the July 8-14 plotted week in the default view. Viz-in-tooltip source, Trend target, State membership field and native target-action filter are checked in the artifact; no browser hover or click was executed.

Visible differences:

- Replica map has more surrounding whitespace and a thin frame/Mapbox attribution; the source map occupies more of the dashboard width.
- Title and footer alignment, font rendering, credit wording and URL presentation differ. The custom black legend circle is slightly larger.
- Replica YoY legend is titled YoY%, shows decimal percentages, and explicitly centers on zero. The source uses a longer caption and integer percentages; in all-positive/one-state views its legend can start above zero or collapse to one value. This causes small shade/legend-range differences without changing the verified metric values or signs.
- Replica Date control shows numeric January 1-July 14 bounds and omits null wording. For the post-context subsets the source card displays All values while the replica card continues to show its native context range. This is a documented control-display difference, not evidence that either REST request changed the global date LODs.

Original comparison provenance binds the untouched author archive to a windows-only export copy. Workbook, PNG and CSV hashes are validated in `cloud-verification.json`; numeric details are recorded in `cloud-data-comparison.json` and `functional-verification.json`. Earlier incorrect Map totals and misleading date-state names are archived in scratch and are not acceptance evidence for this hash.
