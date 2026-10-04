# Cloud review: 2021 WW03 Control Chart

Verdict: **acceptable_delta**. The frozen replica SHA-256 is
`55fc9aaeb2913767cceefc73117eb3cf716bd0759fd2f03f14a7edbf1479f58a`,
built from an empty `TWBEditor("")` with the installed, noneditable Git SDK
`fe9f33b4dfbe5b1ecec7c56d41138a2888971375`.

All four author/replica Summary image pairs and the default Detail pair were
inspected directly. The weekly line geometry, yearly partitions, gray reference
bands, orange/gray point classification, extreme labels and dynamic subtitles
match the source behavior. The one-year view retains the two orange final points;
the five-year view retains the 484 peak and the yearly extreme labels. Default
Detail shows the same `None` title, empty table and upper-right gray Back button.

| REST state | Unique weeks | Complaints | Chart CSV rows per role | Data CSV rows per role | Source Chart/band classification differences |
| --- | ---: | ---: | ---: | ---: | ---: |
| Submitted / 3 years / 1 STD | 146 | 29,631 | 292 | 1,752 | 12 |
| Received / 3 years / 1 STD | 146 | 29,596 | 292 | 1,752 | 17 |
| Submitted / 1 year / 2 STD | 41 | 8,007 | 82 | 164 | 0 |
| Received / 5 years / 3 STD | 250 | 46,342 | 500 | 5,000 | 3 |

The 16 main CSV files cover both Chart panes and the complete auxiliary Data
view for both roles in all four states. Each date has exactly two equivalent
Chart records, and each Data date/year/measure combination occurs exactly once.
Cross-year Data densification produces blank count cells; these are validated
separately from the populated weekly counts. Counts, annual means and sample
standard-deviation limits are independently checked against all 75,513 locked
Hyper records. All original and replica CSV checks pass without relaxing the
source classification comparison.

The original Chart uses the mean of all visible weeks for point classification,
combined with each year's standard deviation. Its gray reference band and Data
view use each year's mean. This source behavior is preserved, so a point's color
does not always describe its location relative to the displayed band. For
example, Submitted / 3 years / 1 STD classifies the week 2018-11-12, count 164,
as In despite its annual lower limit of approximately 176.5161. The independent
two-scope oracle and all counterexamples are recorded in
`source-classification-context.json`.

The two additional Detail CSV files each contain one LF byte and zero data
records. Together with the two Detail PNGs, they prove the default unselected
Detail state is empty. They do not demonstrate a selected drilldown or execute
an action. In total this case binds 10 PNGs and 18 CSVs to the source and frozen
replica hashes through `cloud-verification.json` and `cloud-detail-default.json`.

Accepted visual differences are limited to Summary title and plot padding,
font metrics, omission of the triangular instruction bullet, the SDK footer
attribution and HTTPS link, and the Show Controls button's black text without
the source's gray fill and white text. Detail title/Back font baselines differ
slightly while their native geometry matches the source. This is not a claim of
pixel equality.

Native artifacts verify the parameter-only floating panel toggle, cross-dashboard
Year/Week Number/Dummy selection filter, show-none clearing, empty initialization,
highlight action, rich tooltips and Back destination. No browser click, hover,
selected Detail event, show/hide operation or mobile interaction was executed.
Only the four listed REST parameter states were rendered; the mathematical
oracle additionally covers all 30 parameter combinations.
