# 2021 WW03: Control chart

Article: 2021-01-22; official challenge: 2021-01-19, 2021 week 3. Official WordPress post 4368 establishes the challenge date independently of the downloaded workbook name.

The question is whether weekly consumer complaints are outside the annual average plus/minus a selectable number of sample standard deviations. The date parameter selects submitted-to-company or received dates; Latest X Years selects calendar years relative to the latest *week start* in the selected date basis. All weeks begin Monday, matching the original datasource date options. Each actual weekly count is COUNT of nonnull complaint IDs; all 75,513 source complaint IDs are unique and nonnull. The original extract contains dates from December 2011 through October 2020.

## Independent mathematics

The verifier reads only the locked original Hyper, independently groups Python dates to Monday, filters calendar-year starts, computes each year's mean and statistics.stdev (sample standard deviation, ddof=1), and applies strict inequalities to the yearly band/auxiliary Data scope. The original Chart has a different nested AVG context: its point color and In/Out tooltip use the mean of all visible weeks with each year's sample standard deviation. The verifier independently models that actual source behavior as a second oracle. Missing weeks are not silently filled with zero. The calculation is independently evaluated for all 30 public date/years/STD combinations. Actual Cloud states cover Submitted/3 years/1 STD, Received/3/1, Submitted/1/2 and Received/5/3. Both Chart and Data exports are verified against the relevant complete weekly oracle; the detail table's button data never stands in for the summary population.

## Workbook construction and native contracts

The builder begins with TWBEditor("") and loads only inputs/consumer-complaints.hyper. Author TWBX/TWB is read during analysis and source Cloud comparison only. Two synchronized layers provide the gray line and gray/orange within/outside circles, with Year and an integer Week Number derived from Date to Plot partitioning. Only one weekly identity appears in the Chart view, so lines remain connected and yearly WINDOW_STDEV partitions remain valid. Lower and upper WINDOW_AVG/WINDOW_STDEV bounds form a native field-backed paired reference band. Explicit nested table-calculation addressing retains weekly addressing and yearly partitions.

A native button initially hides the dedicated three-parameter floating container. Chart's on-select filter targets the detail dashboard and clears to none. The explicit Year/Week Number/Dummy mapping preserves selected-week identity: Week Number is DATEPART('week', Date to Plot), and both source and target use this identity. The target action filter starts with impossible Year=0, Week=0, Dummy=NO_SELECTION, so default detail is empty. Dummy highlight and Back navigation remain native contracts. The reference author uses an all-fields cross-dashboard filter; explicit same-identity mapping is an observable equivalent contract for the weekly drilldown scope.

The Heading worksheet provides a rich, parameter-dependent subtitle through public mark labels. Native CSV may include repeated records for the two overlapping mark layers. These duplicates must agree and cannot inflate complaint counts.

## SDK baseline and reusable enhancements

Released Git SDK df8c2a52cd48800fa0a43d936f6946d318f5b953 reproduced three missing public primitives using author-free synthetic fields: field-backed reference bands, cross-dashboard filter targets with explicit clear behavior, and parameter-only native toggle containers. The generic SDK enhancement adds these capabilities and regression coverage; no case-specific SDK entry point is used. The final build uses the exact actual Git installation recorded in evidence/build-provenance.json.

## Acceptance boundary

Acceptance uses Cloud REST images/data states plus native artifacts. No browser click, hover, show/hide event, Back button event, or phone layout is claimed executed. Control-visibility/selection/filter-clearing events are verified from their native source/target/window/container contracts. Full visual acceptance and numerical CSV results are recorded in evidence/visual-review.md and evidence/functional-verification.json.

## Source classification limitation retained faithfully

The author's Chart uses Rows for its nested average inside Within STD Limits?/In-Out, but the gray band's nested average uses weekly addressing partitioned by year. Auxiliary Data also uses each-year addressing. Consequently circle color does not always mean outside the displayed gray band: default Submitted/3/1 has 12 such weekly classifications; Received/3/1 has 17; Submitted/1/2 has zero; Received/5/3 has 3. For 2018-11-12 default, 164 complaints are below the annual lower bound 176.5161, yet the author's Chart classifies In. For 2016-05-30 Received/5/3, 77 complaints lie within the annual band 55.7212..219.4711, yet the author's Chart classifies Out. These are retained source behaviors, not silently corrected formulas. evidence/source-classification-context.json binds complete examples and exact source export hashes. Both annual-band and source-Chart oracles are strict and independent; none of these differences is bypassed by relaxing CSV assertions.
