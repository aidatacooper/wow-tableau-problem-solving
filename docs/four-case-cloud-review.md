# 2020 WW01–WW04 Cloud review

The four earliest unconsumed articles in the current catalogue were reproduced in publication order. All builds start with `TWBEditor("")` and use public SDK APIs with extracted, hash-locked Hyper data. Author workbooks are analysis and comparison sources only.

Acceptance covers Tableau Cloud REST images, parameter states, complete relevant worksheet CSV exports, and serialized action contracts. No browser clicks or hovers were executed. The result for each case is `replicated / acceptable_delta`, with explicit visual differences rather than a pixel equality claim.

| Article date / challenge | Review and paired images | Independent data coverage | Recorded visual differences |
| --- | --- | --- | --- |
| 2020-01-04 / WW01 | [Single click sorting](../iterations/2020-01-04-ww01-single-click-sort/evidence/visual-review.md) | Three sort states; six complete Table exports, 306 pane marks, all 17 subcategories and three metrics | Header raised to 100px for Cloud visibility; spacer, label alignment, zero line, typography and footer |
| 2020-01-11 / WW02 | [Dynamic bar chart](../iterations/2020-01-11-ww02-dynamic-bar-chart/evidence/visual-review.md) | Nine period/metric states; eighteen Chart exports, 234 bar values and formatted labels | Narrower bars, darker selector glyphs, spacing, divider and attribution |
| 2020-01-19 / WW03 | [Time visualisation](../iterations/2020-01-19-ww03-time-visualisation/evidence/visual-review.md) | Both complete day and weekday matrices from both workbooks; weekday 1,047 circles + 82 spans, day 1,495 circles + 322 spans per workbook; all 1,687 latest-year orders | Plot padding, ticks, trendline thickness, footer and saved author axis selection |
| 2020-01-25 / WW04 | [Relative and custom dates](../iterations/2020-01-25-ww04-relative-custom-dates/evidence/visual-review.md) | Four date states; all three KPIs and complete 14/29/59/322-date sales series from both workbooks; duplicate dual-axis CSV rows checked | Selector raised to 100px for Cloud visibility, shorter trend panel, visible selector axis labels/ticks, white background, typography and footer |

Default-state image pairs:

| Case | Author | Replica |
| --- | --- | --- |
| WW01 | [Image](../iterations/2020-01-04-ww01-single-click-sort/outputs/cloud-author.png) | [Image](../iterations/2020-01-04-ww01-single-click-sort/outputs/cloud-replica.png) |
| WW02 | [Image](../iterations/2020-01-11-ww02-dynamic-bar-chart/outputs/cloud-author.png) | [Image](../iterations/2020-01-11-ww02-dynamic-bar-chart/outputs/cloud-replica.png) |
| WW03 | [Image](../iterations/2020-01-19-ww03-time-visualisation/outputs/cloud-author.png) | [Image](../iterations/2020-01-19-ww03-time-visualisation/outputs/cloud-replica.png) |
| WW04 | [Image](../iterations/2020-01-25-ww04-relative-custom-dates/outputs/cloud-author.png) | [Image](../iterations/2020-01-25-ww04-relative-custom-dates/outputs/cloud-replica.png) |

Each review links its full evidence. `export-provenance.json` binds the original author archive to the comparison copy, which only exposes hidden worksheet windows for REST export. `cloud-verification.json` binds the final workbook hash, published IDs, parameter states, image hashes and CSV hashes. Button or selector CSV exports are not used to establish matrix correctness. CSV ordering is not used to establish rendered sort order.

The SDK changes include independent metric panes, header sort controls, virtual Measure Names parameter action sources, native trendlines, correct table-scoped LOD filter semantics, and parameter-control caption visibility. Synthetic regression tests and case origins are documented in [case-driven SDK enhancements](https://github.com/aidatacooper/cwtwb/blob/main/docs/case-driven-enhancements.md).

The cases were built and captured with pinned SDK commit `12aae31b38e3790b57b28b4240a44255a0bb01ee`: 520 SDK tests passed and 25 were skipped; 55 shared case tests passed. [SDK CI](https://github.com/aidatacooper/cwtwb/actions/runs/37043841569) passed. Preserve the accepted workbook bytes: rebuilding changes workbook identity and requires fresh Cloud capture and evidence bindings.
