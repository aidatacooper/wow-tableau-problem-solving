# Net change between two dates (2021 W38)

## Business question
For each Superstore Region, how much did daily sales change between the first and last trading days in a selected date interval? A separate timeframe controls the visible trend history. This is inspired by a stock tracker: select a timeframe, then brush dates to update regional net-change KPIs.

## Why boundary dates alone are wrong
A Region may have no sale on the selected calendar endpoint. Treating that as zero creates a spurious change. The article instead finds the first and last dates with sales inside the inclusive selected interval, independently for each Region. The default today is fixed at 2021-09-20 because this is a static extract; unset range parameters use 1900-01-01 sentinels and resolve to today minus 14 days through today.

## Native solution
Two locked sources contain 9,994 order rows and a five-row timeframe list. Four parameters feed a timeframe boolean filter and a selected-date calculation. Nested FIXED Region LoDs find trading endpoints and total sales there. Aggregate difference and percentage calculations drive the KPI text and sign colours. Trend combines Line and Area on synchronized continuous date axes; stacking is off, and positive/negative reference bands use distinct endpoint calculations. Region order is South, West, Central, East. Three parameter actions write timeframe/min/max date; two True-to-False self-filter actions clear highlighting.

## Independent expected results
The verifier groups raw order rows by Region and calendar day before resolving endpoints; it does not evaluate or import the builder's calculations. Default results are:

| Region | First trading day | Last trading day | Net change | Percent change |
| --- | --- | --- | ---: | ---: |
| South | 2021-09-07 | 2021-09-19 | +49.448 | +60.6218% |
| West | 2021-09-07 | 2021-09-19 | +210.809 | +16.6106% |
| Central | 2021-09-07 | 2021-09-18 | -1,703.208 | -89.0218% |
| East | 2021-09-07 | 2021-09-20 | +6,775.290 | +1158.9062% |

Additional expected July and same-day ranges are recorded in `outputs/expected-range-states.json`. Same-day changes must all be zero. The display timeframe does not change fixed-range KPIs; it only changes visible trend history.

## Released SDK baseline
Built independently from `TWBEditor("")` with cwtwb 0.29.0a1 at commit 23b1df0. No SDK changes or author XML injection. Explicit quantitative date dimensions and bracketed references emit the author's native none:qk instances; an EXACTDATE wrapper around calculated captions was replaced before runtime validation. Text palette registration and a regional rank calculation are case-level API workarounds, not reusable missing primitives. Layered Area explicitly disables breakdown/stacking.

## Acceptance boundary and visual review
Nine automated scenarios cover native contracts and the independent extract oracle. Desktop LOADED and all three Cloud REST states are now verified against the frozen artifact. The Cloud request covers default, July, and single-day parameter states. Original author file must never be modified to expose hidden sheets. If only its dashboard is exposed, compare its rendered KPI labels with replica CSV and the oracle. Font metrics, padding, and decorative line placement may differ; missing regions, incorrect dates, null/blank charts, signs, endpoint amounts, and broken serialized actions are functional failures. Browser clicks have not been executed or claimed.

## Final runtime findings

The initial capture had correct negative-band endpoint values but its fill was covered by the later Area pane. Attaching both conditional bands to that final pane, using its synchronized selected-date axis, restores the sign-dependent fills without changing formulas or data. The final three screenshots confirm negative bands for Central by default and South/West/Central in July. All 18,144 Cloud numeric comparisons pass; full Region-day domains contain 446/852/89 marks. See evidence/visual-review.md for the remaining layout and dotted-boundary differences.
