# WW44 final Cloud REST review

Result: **replicated / acceptable_delta**. Reviewed all six paired dashboard PNGs and all twelve complete worksheet CSVs in the frozen capture.

Replica TWBX SHA256: `628bdc0e96b2c9fb30d8105b4d43103d48404e6539861777feb6c55c73ec27cf`. Author comparison TWBX SHA256: `7d7540155c290657763890888b3bb7c37ae458d8d4f976a42d0aa4c45f1855d0`. `cloud-verification.json` binds each PNG/CSV hash to these artifacts; `export-provenance.json` binds the comparison copy to the untouched source. The comparison transformation only exposes existing worksheet windows, preserving business calculations, data, layout and filters.

| REST state | Completed dates per role | Chart CSV rows per role | Data CSV rows per role |
| --- | ---: | ---: | ---: |
| default | 365 | 754 | 2262 |
| june | 30 | 62 | 186 |
| november | 30 | 62 | 186 |

Default covers January 1-December 30, matching the original native domain bounds, plus twelve month-subtotal keys. Chart exports two panes per date/subtotal; Data exports all six measures per key. June and November each contain thirty completed dates and one subtotal, restricted by actual base Order Date equality-list REST filters. These full worksheets prove the daily matrix; month labels or a dashboard-only export would not.

The independent oracle aggregates all 9,994 locked raw facts without using either workbook's calculations. It separately includes all 366 leap-year calendar dates, of which 322 have 2020 facts; December 31 is outside both workbooks' observed domain. Each export is checked for daily profit, zero-filled Actual Profit, monthly running endpoints, negative Gantt sizes where present, sign colours, monthly profit LOD, year maximum monthly-profit LOD and all month subtotals. Data additionally checks its independent year-running Actual Profit branch and subtotal endpoints. Full-year profit is 93,439.2696; maximum monthly profit is 14,751.8915. The formerly omitted January 31, February 1/29, March 1 and May 31 are now present in both default Data exports; the 365-date requirement was retained.

Default images retain the 4 x 3 quarter/month grid, twelve readable two-line month/amount labels, rising blue and falling red Gantt marks and monthly total bars. June and November images show only the requested month, with readable $8,223/$9,690 labels and corresponding daily sequences. No chart or label clipping was observed. Remaining visual differences are outer padding, font placement, quarter-label spacing, slightly different shared-axis placement in filtered views, and footer credit/link formatting. The replica identifies its SDK build rather than presenting itself as Donna's original. These differences are accepted within the calculation/layout contract; this is not a pixel match.

The native artifact verifies discrete Day-Trunc Data dates, base-date domain completion, explicit local table-calculation addressing, transparent month-label line, synchronized Gantt axes, automatic subtotals and the absence of parameters/dashboard actions. Tooltip and automatic Phone layout are artifact contracts only. No browser click, hover, action execution or mobile render is claimed.

Rejected prior captures remain analysis-only under `scratch/ww44-analysis/round-01`, `round-02` and `round-03`: ignored derived-month REST filters, incorrect year-running direction, and the calculated exact-date substitute's five missing completion dates, respectively. Acceptance uses only the fresh hash above. Released SDK failures and synthetic evidence remain recorded separately; the coordinator supplies the immutable final SDK pin without rebuilding this accepted identity.
