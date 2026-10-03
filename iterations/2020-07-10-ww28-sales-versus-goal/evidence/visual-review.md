# Cloud comparison: acceptable_delta

Artifact SHA256: `5cddaace991779d88ae179d2d29387f2229c2c16cc0f63294cbc1e7579de6b2c`.

All eight full-resolution REST images were inspected as four author/replica pairs: default, Home Office / Furniture, Bookcases, and thresholds 20% / 50%. The replica preserves the main 800 × 900 layout, complete title, threshold controls, pink monthly goal line, dark actual-sales line, July 2019 dotted cutoff and shaded future, colored monthly status strip, readable full-year/month detail table, and black section separators. Home Office / Furniture retains the sparse-parent goals. Bookcases correctly has no goal line, an entirely gray strip, NO GOAL text and blank RESULT. Wider thresholds change the same months to the same green/yellow/gray statuses in both roles. The filtered replica subtitles now show the selected dataset consistently.

All 32 full-sheet CSV exports passed the independent raw-Hyper oracle, with complete keys and metric coverage for both roles. The oracle reads 9,994 actual order lines and 534 unique monthly goals independently; it never sums goals once per order line. Native relationships and all three relationship keys are also checked in the generated artifact.

| State | Table segment/month marks | Data completed leaf/month cells | Monthly line marks | Monthly barcode marks |
| --- | ---: | ---: | ---: | ---: |
| Default | 144 | 2,880 | 48 | 48 |
| Home Office / Furniture | 47 | 235 | 47 | 47 |
| Bookcases | 64 | 105 | 35 | 35 |
| 20% / 50% | 144 | 2,880 | 48 | 48 |

Table CSV covers only the collapsed segment/month view. Full Data CSV verifies the expanded Segment / Category / Subcategory / complete-month domain, distinct subcategory counts, window maxima, financial metrics and Records to Show flags, including 2020 goal-only records and separately identified empty domain-completion cells. Line CSV validates actual/goal values independently at its own monthly grain; Barcode CSV validates every RAG classification. Raw-decimal financial exports are compared within 0.00001, with exact discrete counts. The source's empty formatted zero-goal cells are explicitly distinguished from null business results. File and workbook identities are bound by the Cloud manifest and export provenance; the analysis comparison copy changes only hidden worksheet visibility.

Remaining visible differences are acceptable in the agreed scope: replica axes use abbreviated K amounts rather than full dollar labels and automatically selected date ticks include day/short-year text; the July label is abbreviated. Chart padding and status-strip height differ, row/header weights and alignment differ, and the replica shows slightly more table rows. Footer credits occupy one centered line, the URL lacks the source's blue underline, and pink title text has lighter weight. In Bookcases, the subtitle derives CATEGORY: Furniture from the selected dataset while the source says CATEGORY: All to describe the unset category filter. These differences do not change selected records or calculations. This is not a pixel match.

The three on-select table filter actions, source, dashboard target excluding Table, per-field bindings and show-all clearing, exact date derivations, and noncyclic table-calculation dependency contexts are validated as artifact contracts. REST filter/parameter states do not prove browser clicks, hierarchy expansion, or action execution; none were executed or claimed. Superseded date-grain and subtitle captures remain archived in scratch and are not final acceptance evidence.
