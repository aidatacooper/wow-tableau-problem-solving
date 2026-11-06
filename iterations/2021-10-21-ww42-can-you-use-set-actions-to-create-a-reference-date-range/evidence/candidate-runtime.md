# WW42 candidate runtime checks

The a1 baseline is frozen as `outputs/baseline-a1-replicated-workbook.twbx`.
Its original local report is retained under `baseline-a1/evidence/`; it did not
exercise VizQL. Cloud exposed every state ranked 1 with a 100% share. The SDK's
Text builder dropped explicit table-calculation addressing, requiring a generic
SDK repair. The candidate source commit is recorded in `local-verification.json`.

The final candidate uses public layered-chart APIs to bind both date endpoints
to the same Trend pane. This restored the native date reference band. Its two
line layers retain all 48 months, with only the selected portion purple. Explicit
month addressing makes the only default peak label December 2020 ($96,999.04).
The donut uses pane-local rank colors; its center shows $493,007.99.

Default Cloud totals: nine selected months (October 2020–June 2021), sales
$493,007.99, monthly average $54,778.67, first-to-last change −11.2%.
Top states: California $99,025.33 (20.1%), New York $44,986.03 (9.1%), Washington
$38,240.64 (7.8%). `cloud-verification.json` and `cloud-csv.json` bind the actual
artifact and exported files. The local verifier evaluates six selections from
raw Hyper data; nine negative mutations and one positive control pass.

The default screenshot was inspected. Layout, wedge order, map palette and
typography differ from the author but preserve the business answer. This supports
`acceptable_delta` for the observed default state, not pixel matching.

No browser selection, clear event, Ctrl-select or live linked-view update was
executed: user MFA is unavailable. REST data and formula scenarios do not prove
event handling. Functional status remains partial. Final Desktop/corpus and
independent-review evidence are maintained separately when those gates finish.

Final integration: Desktop LOADED and the 50/50 existing corpus report are now
bound to this frozen artifact. Independent review found no confirmed defects.
SDK PR #22 is merged. A fresh pip VCS installation of the exact requirements
pin completed successfully, and the full isolated validator passed using that
installed package (no source checkout needed). Two provenance tests cover pip
VCS metadata and plain-wheel installations without inventing a commit ID.
