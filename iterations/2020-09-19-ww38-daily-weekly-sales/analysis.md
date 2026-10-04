# Daily and weekly ticket sales

The article is dated 2020-09-19. Official WordPress post 3989 is week 38, published 2020-09-16; the original workbook name has 2020-09-09 while its dashboard correctly uses 2020-09-16. These filename dates are not additional business dates.

The untouched original contains 5,040 date-scaffold records for 12 events. Each event starts on its launch week Monday and ends on its event week Sunday. Empty Sold Amount records are zero for daily ticket sales. Week numbers are relative to the Monday of launch, not calendar week numbers. There are 720 event/week aggregates across the complete input.

The main Viz has a continuous day-position Gantt layer and a separately grained weekly Gantt layer. Monday=1 and Sunday=7. Launch and event dates are dark gray; ordinary days are white. The weekly strip spans 0?1 and its green color encodes running weekly sales divided by all sales for the same event. The cumulative and nested total calculations both address Week No From Launch; they partition by event. Daily date details are attached only to the daily pane.

Comparison changes grouping from Event Year to YoY Event. Event Group chooses All, Spring or Fall from the event quarter. REST acceptance covers default, YoY, Spring, and Fall+YoY. No browser parameter click or hover is claimed. Tooltip and native controls are checked in the artifact.

The original diagnostic daily sheet intentionally filters to three named events, while its weekly sheet filters to 2020 EVENT #6. These restrictions are preserved. Their CSVs cannot establish the entire visualization; the main Viz export and independently recomputed complete raw daily/weekly oracle establish the larger scope.

The build reads only the extracted Hyper and starts TWBEditor(""). The original workbook is used only for analysis and a windows-only comparison export copy, bound by export-provenance.json. Rebuilding after capture requires new publication and all evidence hashes.

The source uses a four-step green gradient. The initial released SDK baseline supports a continuous custom gradient; this visual detail is a generic stepped-color capability request, not a business calculation blocker. The current candidate uses the new general stepped-color API with num_steps=4. Final all-four-state Cloud CSV and paired PNG review passes with documented acceptable_delta; see evidence/visual-review.md.
