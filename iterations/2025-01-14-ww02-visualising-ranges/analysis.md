# 2025 Week 2 — Visualizing Ranges

## Identity and scope
Article: https://donnacoles.home.blog/2025/01/14/visualising-ranges/ (2025-01-14).
Official challenge: https://www.workout-wednesday.com/2025w2tab/ (2025-01-08, Sean Miller).
Author: https://public.tableau.com/views/2025_01_08_WW02_Visualising_Ranges/2025_01_08_WW02_Visualising_Ranges.
Fresh origin/main tree and all open repository issues were checked before claiming; no matching active case/issue. The imported dataset name WoW2024Wk49 is an upstream dataset label, not this challenge's year.

## Business question and complete requirements
Summarize the daily hourly distribution of glucose across the measurement period. The reader must see the typical level, variability, extremes, and the 80–180 mg/dL normal reference range.
Official requirements are a 1300x600 dashboard, one worksheet, hourly median as a dashed line, shaded/layered 5th/25th/75th/95th percentile ranges, and dotted reference lines or a band for 80–180. There are no required selectors, parameter changes, drilldowns, or reset controls. Standard tooltip inspection remains a business verification step.

## Analysis-only author inspection
The author package includes one 131072-byte Hyper file; inputs/source-lock.json locks both archive and extracted bytes. Hyper schema has Device Timestamp (timestamp) and Glucose mg/dL (bigint). There are 4319 readings and all 24 hours.
The author workbook contains an auxiliary analysis table and one dashboard chart. Our output contains only the required chart worksheet. Each hourly group computes MIN, PERCENTILE(.05/.25/.5/.75/.95), MAX. Median is a black dashed line over six unstacked areas, ordered Minimum, P05, P25, P75, P95, Maximum. Colors in that order are white, #d2e1f3, #a9c1df, #7a93b9, #a9c1df, #d2e1f3. White minimum masks the below-minimum region; reverse fold layering puts the median on top. Percentile areas have full opacity and no stroke. X-axis extends 0–26, ticks every 3 hours. Values and direct percentile labels remain visible.
The article explicitly says vertical gridlines are an unintended Public rendering nuance; they are omitted here. The 80 and 180 orange dotted reference boundaries are required and retained.

## Construction boundary and design
Builder starts from TWBEditor("") and uses only public SDK methods and the extracted Hyper. No author XML/image is opened or copied by the builder. Native aggregate percentile calculations remain in Tableau; no precomputed summaries replace them. Continuous DATEPART(hour) is the semantic equivalent of the author's continuous hour datepart. A constant calculated field averaged for each reference line gives exactly 80/180 without raw XML. Palette keys must be quoted full field references. Public configure_layered_chart, configure_worksheet_style and datasource color palette APIs express the layering, synchronization, opacity, axis hiding and dotted/dashed styles.

## Numerical verification
verify_replication.py reads all raw readings and groups by hour in Python. Sorted linear interpolation at (n-1)*p is compared with independently executed Hyper PERCENTILE_CONT queries for all hours. It checks 168 values (min, five percentiles, max across 24 hours), cardinality and monotonicity; no mismatch. Generated formulas, area membership, line styles, palette, reference bindings, canvas and the exact packaged data hash are structurally checked. evidence/verification.json contains every expected hourly value. This oracle does not establish Tableau rendered values; parent must compare export/tooltip observations against it.

## SDK baseline and final source
Latest non-yanked stable was queried from PyPI: 0.28.0. First isolated attempt lacked tableauhyperapi, produced unknown-field warnings and a verifier import failure; retained as an environment failure, not an SDK gap. With tableauhyperapi explicitly present, the same builder/verifier passes on 0.28.0.
Selected source explicitly uses CWTWB_SRC and PYTHONPATH = C:/Users/imgwho/Desktop/project/cwtwb/src. Actual tested version is 0.29.0a3. The first implementation probe occurred while that checkout was dirty; no claim is based on that probe. Earlier static passes did not establish Desktop compatibility: the parent recorded FAIL D2E8DA72 on commit 2b72232245959934281c49308f5c3b2fca8fc519, with mark-line-pattern rejected by the loader enumeration. This is a generic missing document-format manifest bug, not a case API usage error. The genuine author workbook uses the same attribute together with PatternedLineMarks. Upstream SDK PR25 adds that manifest automatically; this case now tests clean commit 056050c8e95f5fbe3560886e566c34aee53b40b0 without changing its builder or editing the SDK. The verifier requires PatternedLineMarks and proves a copy with the flag removed is rejected. Historical evidence is retained, with new source/artifact hashes in evidence/manifest-fix-20261114.json.

The copied desktop-corpus.json and desktop-corpus-evidence.json report 50 LOADED on the pre-fix source 2b72232245959934281c49308f5c3b2fca8fc519. They are historical baseline evidence only; they do not establish a full Desktop regression pass for 056050c8e95f5fbe3560886e566c34aee53b40b0. Current-source Desktop and rendered acceptance remain parent-owned and pending.

## Status and remaining acceptance
Functional status is replicated and visual status acceptable_delta. The parent opened the frozen fc29870d0ac45a7615fa0d599c01d38de925a28fa349aa43ea3e9df54e565a6c artifact in real Desktop: LOADED. The dashboard screenshot confirms the nested percentile areas, visible black dashed median, direct percentile labels and dotted orange 80/180 boundaries. Comparison with the actual article reference accepts typography and direct-label differences, including the absent separate Median end label; the dashed median remains identifiable. The real Hour 15 / 75th Percentile tooltip shows 162.0. Desktop Copy > Crosstab supplies all 168 displayed values across 24 hours, matching the independent oracle within one-decimal rounding tolerance 0.050000001. No parameter, selection or reset interaction is required. Evidence includes the actual TSV, dashboard/tooltip screenshots, PID and hashes. No requirement was removed to obtain passing checks.

The primary artifact remains unchanged and was built from fix-head 056050c8e95f5fbe3560886e566c34aee53b40b0. requirements.txt pins merged SDK PR25 commit bbd749f25a5375889a66a8cd72aaaee129810353, also used by shared workflow PR65. Exact-pin validation rebuilds only in temporary copies. The full post-fix Desktop corpus is still a parent-owned release gate; earlier 50-LOADED evidence is not attributed to the fixed SDK. Metadata's legacy cloud_author/cloud_replica slots point to local reference/Desktop images and do not claim Cloud rendering.
See evidence/desktop-acceptance.md for precise steps and PROGRESS.md for resumable state.

## Reference image caveat
The local dashboards PNG was inspected and is a Tableau loading placeholder, so it is not usable visual evidence. evidence/article-reference.png is the downloaded article reference image, inspected to confirm the layered blues, dashed median and orange normal boundaries, with provenance/hash in adjacent JSON. It is analysis-only, not a generated replica screenshot.
