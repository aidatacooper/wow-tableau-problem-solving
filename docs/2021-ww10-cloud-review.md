# 2021 WW10 Cloud review

Case: **Can you build a "must include" filter?** (`wow-2021-ww10-must-include-filter`)

Result: `replicated / acceptable_delta`, `cwtwb_result: pass`, tested on
released cwtwb **0.27.1** (`6f22023`).

## What was checked

Cloud REST capture of the dashboard default state for both roles, plus complete
worksheet CSV exports of the replica's Bars and BANs views. The author workbook
publishes only the dashboard view, so the author side is the dashboard PNG; no
author worksheet CSV exists to compare. No browser click, hover, drag or clearing
execution is claimed.

| Artifact | Path |
| --- | --- |
| Author dashboard | `outputs/cloud-author.png` |
| Replica dashboard | `outputs/cloud-replica.png` |
| Replica Bars CSV (5,009 orders × 2 measures) | `outputs/cloud-replica-bars.csv` |
| Replica BANs CSV | `outputs/cloud-replica-bans.csv` |

## Default-state agreement

| Metric | Author | Replica | Oracle |
| --- | ---: | ---: | ---: |
| # ORDERS | 5,009 | 5,009 | 5,009 |
| % OF TOTAL ORDERS | 100.0% | 100.0% | 100.0% |
| AVG ORDER AMOUNT | $459 | $459 | 458.615 |
| AVG ORDER QUANTITY | 8 | 8 | 7.561 |

The displayed values are formatted; the raw replica CSV values are
`458.614665662` and `7.560990218`, which match the locked-data oracle exactly.

## Functional proof beyond the default state

`evidence/functional-verification.json` records a real two-stage execution: the
two sets were pre-populated with one product each, published, and exported over
REST. Bars returned exactly the oracle's two qualifying orders
(`CA-2017-129147`, `US-2017-103905`) and BANs returned
`# ORDERS = 2`, `% OF TOTAL ORDERS = 0.000399281`,
`AVG ORDER AMOUNT = 338.821`, `AVG ORDER QUANTITY = 13.5`.

Order `CA-2017-129147` has three line items, one of which is neither selected
product; its reported Sales of 609.438 therefore proves the totals are computed
over **all** lines of qualifying orders rather than only the matching product
lines. This is the crux of the case and is the failure mode the article warns
about.

## Visual differences

- Mark colour is the default blue instead of the author's Nuriel Stone palette.
- The two controls are native set controls (`set_control` layout node) and both
  read `All` in the default state, matching the author.
- Minor row-height and spacing differences.

None of these change the business answer, interaction outcome or readability.
