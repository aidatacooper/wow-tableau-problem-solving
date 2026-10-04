# Cloud review: mobile calendar picker

Result: **replicated / acceptable_delta** within the REST-state and native artifact-contract scope. The result is not pixel-identical.

Accepted TWBX SHA-256: `74b282f80fda0bc0cc519f4dfe7927bcae6a85044dc5fb67e4d7f5360e4ea8f7`.

`cloud-verification.json` binds both published workbooks, all eight paired dashboard PNGs and seventy-two worksheet CSV files to their hashes. The comparison author workbook only exposes existing hidden worksheet windows; `export-provenance.json` proves all other XML content and archive members are unchanged.

| REST state | Complete independent verification |
| --- | --- |
| June 2019, 6–18 | All thirty calendar cells and colors; thirteen daily rows with three metrics; complete Sales/Profit/Quantity totals; selected period and adjacent-month targets. |
| July 2019, 1–7 | All thirty-one dates; seven complete daily metric rows and totals; both endpoint highlights. |
| Leap February 2016, 10–29 | All twenty-nine dates including leap day; twenty daily rows and totals; full-year navigation dates. |
| December 2018, 18–31 | All thirty-one dates across six calendar rows; fourteen daily rows and totals; January 2019 next-month target. |

The verifier independently reads all 9,994 order facts and all 1,461 distinct dates in the locked calendar domain. Every author and replica export is checked: 242 paired calendar cells, 24 BAN metric totals, and 108 paired daily rows containing 324 metric values. The complete Year and Month picker domains, grid coordinates, selected states, period endpoints, displayed month and both navigation dates are also checked. Line CSV retains full numerical precision; the dollar-rounded BAN display does not replace the daily/full-precision oracle. Calendar duplicates are not joined into inflated fact sums.

All four image pairs were inspected. Monday–Sunday order, full-cell pale-pink range shading, strong endpoint shading, all calendar date labels, readable selected dates, all three totals and the three daily curves are present. Navigation is now rendered as readable gray Text chevrons. Numerical trend ticks are restored while axis titles and the date axis remain hidden, matching the author's intent.

Five native parameter actions are checked for on-select activation, declared source instances, intended real parameter targets, Attribute aggregation and keep-current values on clear. The date-selection source is the actual `ATTR(Date Control)` instance, matching the author's Attribute source. The earlier bare source was rejected even though REST snapshots had correct values. Three true-to-false deselection actions verify their same-sheet targets, mappings and auto-clear contracts. The native initially hidden year/month picker and toggle identities are preserved in the Phone device layout, whose complete zone tree equals the default layout.

Remaining visual differences are the shorter bold title; chevrons instead of the author's circular arrow PNGs; the textual Month button instead of a hamburger icon; a longer metric-section caption; full numerical trend ticks instead of K abbreviations; lighter/fewer panel separators; and condensed footer credits/link styling. The copied Phone zone positions preserve this build's default layout rather than matching every author's custom Phone coordinate. These differences do not change the displayed dates, values or stored action targets.

Cloud images cover the default dashboard layout at high REST resolution. REST parameters select the four captured states directly. This review does not claim an actual Phone-browser render, opening the hidden picker by clicking, executing the two-click date selection, or replaying navigation clicks. Those events, targets and clear behaviors are covered by the native artifact contract rather than browser interaction.
