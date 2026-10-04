# 2021 WW06 Cloud comparison

Verdict: **acceptable_delta**. The reviewed replica SHA-256 is
`0cf123a0e32ae95892e9283c2cc7a31cdfcb18205d0c969beed5f168b5656d37`.
The exact SDK Git installation and builder hash are recorded in
`build-provenance.json`; the published source and replica hashes, views, two PNGs
and two CSVs are bound by `cloud-verification.json`.

The reviewed workbook was built and published with the actual noneditable Git
SDK `85643b0866f6d3b3cdf07c3f61762cd586a67589`. The final capture was
independently rechecked against the frozen output and locked raw input. Both
final PNGs were directly inspected; all 192 complete-table CSV cells and native
contracts passed, with no workbook rebuild during or after capture.

Both full dashboard images were directly inspected. The report contains all
12 months in calendar order and all eight measures in the source order. Sales,
delta, red/green percentages, comparison symbols, green best dates, red worst
dates and six TOP/six BOTTOM labels match. The gray alternating row bands and
full-width table remain visible, with footer positions matching the source.
An earlier candidate omitted entire-view fitting and centered all footer text;
that capture was archived for diagnosis and replaced using existing public
layout APIs.

Both complete Table CSV exports have 96 records: exactly one cell for each
month/measure pair, with no duplicate or missing cells. All 192 author/replica
cells pass independent comparison against the 5,899 locked raw Order Date/Sales
records. Raw monetary values are checked within 0.000001 and raw percentage
ratios within 0.00000001; integer comparison/rank values and date serials are
exact. CSV values retain numeric dates and numeric signs rather than the
displayed date/symbol formats. Native artifacts independently verify those
display formats and all eight separate two-step color domains.

Daily extrema are computed from current-year observed dates only; no missing
day is treated as zero. Latest tied-date selection matches the source MAX date
calculation. Rank uses descending competition rank and SIZE()/2, with the
source nested Columns addressing. November is rank 1 and February rank 12.
This CSV scope proves the complete visible monthly report, not a button or
partial data table.

Remaining visual differences are title weight and top spacing, centered month
labels where the source uses left alignment, small font/row-spacing differences,
and the SDK attribution and HTTPS footer URL. These are accepted differences;
pixel equality is not claimed. The full dashboard is 1200 by 800 and the native
table rectangle matches the source. Phone layouts are outside this review.

The source has no parameters or action events. Only the default REST state was
captured. No browser click, hover or mobile interaction was executed, and REST
exports are not described as browser interaction tests.
