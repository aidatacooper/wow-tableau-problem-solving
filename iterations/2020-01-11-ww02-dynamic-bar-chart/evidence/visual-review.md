# Cloud REST review

Result: acceptable_delta. The reviewed replica is SHA-256
`d6df2322340c537c70a5be0f7e84d097e8341acb31f198902dbd181495605042`.
The captured author comparison archive is an analysis-only copy exposing
the original Chart worksheet for data export; its relationship to the
downloaded original is recorded in export-provenance.json.

The default monthly Sales images agree on all twelve bars and rounded dollar
labels, including January $43,971 and November $118,448. The three metric
colors match the official purple, green, and cyan palette. The weekly
Profit Ratio state includes the two negative bars (-2.5% and -5.3%) and
the partial opening week. The daily Items Per Order state has thirteen
bars with matching values, including 9.6 on 12/18 and 3.0 on 12/26.
Monthly Profit Ratio and the other exported state images preserve the
expected active metric and date headers. All nine states were exported
for both author and replica.

The dynamic title now identifies the selected metric and period; the Date Period
control hides its redundant caption. Remaining visual differences: the replica
has narrower bars, more whitespace below its top controls, and lighter typography.
Selector circles are text glyphs in dark
gray instead of the author's larger colored shape marks. The author has
a gray divider above the plot; the replica omits this decorative divider.
Attribution text and the reference link have different size and placement.
These deltas do not obscure any metric, period, or selected measure.

The data check is independent of visual inspection: cloud-data-comparison.json
matches each dated Chart CSV mark and active formatted label to an independent
fact-level Hyper aggregate across all nine combinations, checking all eighteen
exports. Monthly states contain twelve bars, weekly states fourteen bars,
and daily states thirteen bars because one day contains no orders. CSV row
ordering is not used to prove the visual order. Selector/button CSV is not
used as metric evidence.

Acceptance uses REST parameter states and artifact contracts. The verifier
checks select events, Selector source, Selected Measure target, virtual Measure
Names source, keep-current clearing, and the True-to-False self-filter's
show-all clearing. No browser click, hover, or tooltip execution is claimed.
