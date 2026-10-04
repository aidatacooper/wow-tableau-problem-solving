# 2020 WW30-41 Cloud review

Ten cases were selected in ascending unused article-date order after WW29: WW30, WW31, WW32, WW33 and WW36-41. Week numbers are official challenge identities, not a claim that the articles cover every intervening week. The WW33 author workbook is labelled WW34; its official challenge snapshot and article establish WW33.

Every builder starts with `TWBEditor("")` and uses public SDK APIs. Author TWB/TWBX files are analysis, extraction and independently published comparison inputs; builders never read them. Source comparison copies only expose hidden worksheet windows, with business XML and extract hashes independently checked.

| Challenge | Article date | Official challenge date | Scope |
| --- | --- | --- | --- |
| WW30 | 2020-07-24 | 2020-07-21 | State-to-city set drill-down and scatter |
| WW31 | 2020-08-01 | 2020-07-29 | Olympic country ranks, host indicators and compound tooltip contracts |
| WW32 | 2020-08-07 | 2020-08-04 | Daily COVID cartogram and normalized rolling curves |
| WW33 | 2020-08-12 | 2020-08-11 | Monthly connected scatter and insights action contracts |
| WW36 | 2020-09-06 | 2020-09-02 | County radius selection, resource totals and native set control |
| WW37 | 2020-09-11 | 2020-09-08 | Year-on-year state map and date-subset weekly trends |
| WW38 | 2020-09-19 | 2020-09-16 | Daily/weekly event sales and year-on-year states |
| WW39 | 2020-09-26 | 2020-09-22 | Mobile-sized calendar, date controls and metric trends |
| WW40 | 2020-10-03 | 2020-09-30 | NFL sorting, pagination and season drill-down states |
| WW41 | 2020-10-09 | 2020-10-07 | Dynamic per-category reference lines and ranking cards |

Acceptance covers Cloud REST images and declared worksheet CSV exports, independent full-input calculations, and native artifact contracts. Action events, sources, targets and clearing behavior are checked in the workbook; no browser click, hover, filter-card manipulation or mobile-browser execution is claimed. Each case is `replicated / acceptable_delta`, with its remaining differences documented; these are not pixel-identical replicas.

The final evidence contains 36 paired REST states, 72 PNGs and 286 worksheet CSV files. Empty or restricted author diagnostic exports are explicitly excluded as data proof. Shared repository tests: 60 passed. The catalogue contains 69 active cases.

## Data and functional coverage

WW30 checks all 8,399 facts, 48 state aggregates and independently derived city drill-down results. REST default/California/Texas exports validate the state-level scatter; ordinary State filtering does not assign the selected-state set or execute drill-down events. The set action and clearing contracts are checked separately.

WW31 preserves 1,242 country/year medal records, 33,203 athlete medal facts and 28 host records in separate logical tables. Full country-rank paths, host inclusion, all three medal measures and complete athlete medal groups are independently checked. Default and 2008/2016 exports cover five worksheets per role. The author's Top 10 Countries CSV is empty in all three states: it proves no ranking values. That target's filter/context contracts and raw-data ranking oracle are distinguished from the nonempty exported worksheets; no tooltip hover is claimed.

WW32 checks all 51 mapped states/DC across 153 locked days (7,803 state/day keys), separately locked cartogram geometry and normalized seven-day rolling averages. The author's Map CSV is empty, and applying State filters to its auxiliary Data worksheet turns selected state labels null. Therefore each author Data export deliberately remains unfiltered (52,785 long-form rows), retaining all mapped keys and explicitly excluding unmapped provinces. Replica Map exports cover 7,803/153/153 keys under default/California/Texas; PNG requests use State filters for both roles. The capture manifest records the actual distinct CSV filter scopes. The first six incomplete rolling windows remain null, not partially averaged.

WW33 checks all 9,994 facts and 72 category/month points over 2018-2019. Default/Technology/Furniture exports contain 72/24/24 scatter points per role. All six Insights CSVs are empty under the initial empty selected-category set, matching the source; they prove no insights values or action execution. All four extrema per category and their dates are independently checked, alongside native single-select/clear action and nested calculation contracts.

WW36 checks all 3,142 locked counties, full resource totals and complete percentile partitions: global county tables and separate mainland/Alaska/Hawaii maps. Default/50-mile/250-mile REST states retain the author's initial All-members set. Changing radius alone does not select a county. Five independently calculated single-county radius scenarios and the native DISTANCE/set/action contracts are recorded separately, without claiming runtime single-county set changes. Full Cloud county ranks were required: early all-100% Alaska/Hawaii results were rejected, and the final SDK gives differing worksheet table calculations distinct native contexts.

WW37 checks all 486,872 subscription facts and four exported states. The source has a locked January 1-July 14 context and a Full Weeks filter. REST comma-separated date lists filter records after that context; they do not replace the range or execute a daily-grain switch. All actual exports remain Weekly and Wednesday-aligned. Full map and trend checks cover default (185,341/165,191 CY/PY), California (19,528/17,600), June dates (22,134/15,197), and May-June dates (44,323/29,651). Dynamic daily/Monday switching and tooltip filtering are raw/native-contract-only checks.

WW38 checks all 5,040 daily sales facts, 12 events and 720 observed raw weekly aggregates. The main padded Viz exports contain 936 default weekly marks, 258 Spring and 468 Fall marks, with all daily/weekly/YOY states checked independently. Author CHK diagnostics cover only three daily events or one 2020 weekly event; they are not used as proof of the full matrix. The restored native axes, fit and four-step green palette are reviewed in all eight PNGs.

WW39 checks all 9,994 facts and 1,461 unique scaffold dates, full calendar membership/colors, selected-period totals and daily Sales/Profit/Quantity under default/July/leap-February/December. Nine complete worksheets are exported per role/state; navigation CSVs use explicit full-date columns rather than the first CSV cell. Default desktop REST renders use a 350-by-700 mobile-sized canvas. A custom Phone layout preserves the generated default zone identities, hidden pickers and show/hide buttons. Its geometry has a documented source difference; neither mobile-browser rendering nor date-button clicks are claimed.

WW40 checks all 40,736 plays and 556 players. Six states validate all four metrics for the complete selected player/season groups, page two, ascending yards, descending average and the final touchdowns page. Expanded source partitioning can include 11 player IDs, with all three selected seasons checked independently. Header bindings/direction, current/total/previous/next page values and actual mark-source instances (including DD Level), parameter targets and clear behavior are checked; control CSVs do not prove the table. Shelf-only sorting that paginated the wrong members was rejected and replaced by the SDK's native computed member sorting.

WW41 checks all 9,994 facts, 16 quarters by three categories, and three metric states. Whole-category ranking cards use the correct weighted/full-record grain, while reference lines use the average of rounded quarter metrics; these are independently calculated rather than conflated. All actual quarter/category reference values must be present and match the oracle. Blank Cloud views were rejected. Generic parameter dependency and temporal addressing fixes restore the complete quarter calculation; binding the ranking pane's two constant address dimensions restores the three cards. The final verification cannot pass on empty Line or card CSVs.

## Reproducibility

The case environment uses SDK Git commit `eb1380d5da9c1b1bf1b306128cb8397150ba1a53`, version 0.27.1, without an editable dependency. SDK regressions: 738 passed, 25 skipped; [SDK CI passed](https://github.com/aidatacooper/cwtwb/actions/runs/37191478304). Each case records an isolated rebuild audit with only its builder, verifier, metadata and locked inputs, initially zero TWB/TWBX files available. Those rebuilds create separate artifacts and leave accepted Cloud workbook identities and hashes frozen.

SDK improvements and their source cases are documented in [case-driven enhancements](https://github.com/aidatacooper/cwtwb/blob/main/docs/case-driven-enhancements.md).

## Paired default renders and detailed reviews

### WW30

[Detailed review](../iterations/2020-07-24-ww30-set-action-drill-down/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-07-24-ww30-set-action-drill-down/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-07-24-ww30-set-action-drill-down/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW30](../iterations/2020-07-24-ww30-set-action-drill-down/outputs/cloud-author.png) | ![Replica WW30](../iterations/2020-07-24-ww30-set-action-drill-down/outputs/cloud-replica.png) |

### WW31

[Detailed review](../iterations/2020-08-01-ww31-olympic-rank-bump-chart/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-08-01-ww31-olympic-rank-bump-chart/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-08-01-ww31-olympic-rank-bump-chart/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW31](../iterations/2020-08-01-ww31-olympic-rank-bump-chart/outputs/cloud-author.png) | ![Replica WW31](../iterations/2020-08-01-ww31-olympic-rank-bump-chart/outputs/cloud-replica.png) |

### WW32

[Detailed review](../iterations/2020-08-07-ww32-covid-state-cartogram/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-08-07-ww32-covid-state-cartogram/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-08-07-ww32-covid-state-cartogram/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW32](../iterations/2020-08-07-ww32-covid-state-cartogram/outputs/cloud-author.png) | ![Replica WW32](../iterations/2020-08-07-ww32-covid-state-cartogram/outputs/cloud-replica.png) |

### WW33

[Detailed review](../iterations/2020-08-12-ww33-connected-profit-quantity-scatter/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-08-12-ww33-connected-profit-quantity-scatter/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-08-12-ww33-connected-profit-quantity-scatter/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW33](../iterations/2020-08-12-ww33-connected-profit-quantity-scatter/outputs/cloud-author.png) | ![Replica WW33](../iterations/2020-08-12-ww33-connected-profit-quantity-scatter/outputs/cloud-replica.png) |

### WW36

[Detailed review](../iterations/2020-09-06-ww36-counties-within-radius/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-09-06-ww36-counties-within-radius/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-09-06-ww36-counties-within-radius/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW36](../iterations/2020-09-06-ww36-counties-within-radius/outputs/cloud-author.png) | ![Replica WW36](../iterations/2020-09-06-ww36-counties-within-radius/outputs/cloud-replica.png) |

### WW37

[Detailed review](../iterations/2020-09-11-ww37-year-on-year-trend/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-09-11-ww37-year-on-year-trend/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-09-11-ww37-year-on-year-trend/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW37](../iterations/2020-09-11-ww37-year-on-year-trend/outputs/cloud-author.png) | ![Replica WW37](../iterations/2020-09-11-ww37-year-on-year-trend/outputs/cloud-replica.png) |

### WW38

[Detailed review](../iterations/2020-09-19-ww38-daily-weekly-sales/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-09-19-ww38-daily-weekly-sales/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-09-19-ww38-daily-weekly-sales/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW38](../iterations/2020-09-19-ww38-daily-weekly-sales/outputs/cloud-author.png) | ![Replica WW38](../iterations/2020-09-19-ww38-daily-weekly-sales/outputs/cloud-replica.png) |

### WW39

[Detailed review](../iterations/2020-09-26-ww39-mobile-calendar-picker/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-09-26-ww39-mobile-calendar-picker/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-09-26-ww39-mobile-calendar-picker/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW39](../iterations/2020-09-26-ww39-mobile-calendar-picker/outputs/cloud-author.png) | ![Replica WW39](../iterations/2020-09-26-ww39-mobile-calendar-picker/outputs/cloud-replica.png) |

### WW40

[Detailed review](../iterations/2020-10-03-ww40-football-table-enhancements/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-10-03-ww40-football-table-enhancements/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-10-03-ww40-football-table-enhancements/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW40](../iterations/2020-10-03-ww40-football-table-enhancements/outputs/cloud-author.png) | ![Replica WW40](../iterations/2020-10-03-ww40-football-table-enhancements/outputs/cloud-replica.png) |

### WW41

[Detailed review](../iterations/2020-10-09-ww41-per-dimension-reference-lines/evidence/visual-review.md) | [Cloud manifest](../iterations/2020-10-09-ww41-per-dimension-reference-lines/evidence/cloud-verification.json) | [From-zero audit](../iterations/2020-10-09-ww41-per-dimension-reference-lines/evidence/zero-build-verification.json)

| Author | Replica |
| --- | --- |
| ![Author WW41](../iterations/2020-10-09-ww41-per-dimension-reference-lines/outputs/cloud-author.png) | ![Replica WW41](../iterations/2020-10-09-ww41-per-dimension-reference-lines/outputs/cloud-replica.png) |
