# 2024 Week 13 — Segmented Bar Chart

## Identity and task

Official challenge: https://www.workout-wednesday.com/2024w13tab/ (2024-03-26).
Article: https://donnacoles.home.blog/2024/03/28/can-you-build-this-segmented-bar-chart/ (2024-03-28).
Author workbook: https://public.tableau.com/views/2024_03_27_WW13_Segmented_Bar_Chart/Segmented_Bar_Chart.
Selection used freshly fetched origin/main catalogue and article index, checked against local case metadata. No active iteration existed for this article when claimed.

Business question: how do the total sales of 17 sub-categories compare, and how much of each total was contributed by each of the four years? A total bar and a shorter-height segmented bar share the same horizontal scale. The total bar is directly above its annual segments. Labels align to the total bar. Sort by descending total sales. The official requirements specify one sheet, a 1000x800 dashboard, spacing beneath each pair, and matching tooltip content. No filters or selection actions are required. Hover remains an observable acceptance requirement, not inferred from XML alone.

## Analysis boundary and data

The author TWBX and article were inspected only during analysis. `prepare_case.py` extracted the packaged Hyper. `inputs/source-lock.json` binds its SHA256 and author archive SHA256. The extract has exactly three columns (Order Date, Sub-Category, Sales), 10,194 rows, 17 sub-categories, and 2021–2024 dates. The builder opens only this extracted data and an empty `TWBEditor("")`. All authoring uses public cwtwb APIs; no XML editing, author-workbook import, image chart or pre-rendered chart.

The author solution uses cumulative Sales on columns, separate aggregate constants MIN(1.5)/MIN(0.5) on a synchronized row axis, and Sales as a right-aligned axis-unit mark size. Year appears only on the segmented pane. Therefore each annual mark ends at its cumulative sum and extends left by its actual annual sales; the total pane has a single sum and extends back to zero. The fixed row range -0.3..1.5 supplies the lower gap, and bars drawn from zero to 1.5 versus 0.5 yield the different heights. The year table-calculation addressing partitions by sub-category. The article explicitly notes an old incorrect cumulative tooltip; this reconstruction deliberately displays the annual SUM(Sales), not RUNNING_SUM.

## Implementation and numerical acceptance

`build_replication.py` creates one native layered Bar worksheet, two panes, five calculated fields, a fixed 1000x800 dashboard and pane-specific rich tooltips. It retains the tan bars and cream background. `verify_replication.py` does not import the builder. It independently sums every raw row in Python and compares all 68 annual sums to GROUP BY results from the embedded Hyper. It validates exact formulas and native addressing, each size/LOD/axis encoding, descending sort, raw annual tooltip binding, dashboard dimensions, and source identity. It exports all annual sums, totals, segment starts/ends and shares to `outputs/numerical-acceptance.csv` for Desktop cross-checks. It checks that every category's annual segments meet without gaps, end at its total, and sum to 100%.

Total sales: 2,326,534.3543. Highest total category: Chairs. XML and this constrained numerical oracle do not execute Tableau calculations or establish rendered acceptance; Desktop and hover remain pending.

## SDK provenance and runs

Latest non-yanked PyPI stable queried on 2026-11-14 is 0.28.0 (`evidence/pypi-stable.json`). The first stable environment lacked tableauhyperapi: its attempted build and failed verifier are preserved in `evidence/stable-028.json`; that result is an environment deficiency and must not be called an SDK regression. A complete stable baseline follows separately.

Selected source is explicitly C:/Users/imgwho/Desktop/project/cwtwb/src, version 0.29.0a3, Git HEAD 833cf41125396ec92e92f44bc2163c2028bc5261 with existing uncommitted changes. Full package manifest/hash, dirty paths and source diff are preserved with each source run. This is a release-preparation checkout, not a claim that a3 is published or that HEAD alone reproduces the dirty source. No SDK files were changed by this case.

## Completion boundary

Static build, XSD, phase boundary, metadata and numerical checks must pass before handoff. Parent owns serialized Desktop loading, visual checks, tooltip hovers, final source pin/retest, corpus checks, index refresh, independent commit and push. Keep functional_status partial and visual_status not_evaluated until that evidence is captured. No partial case is counted as solved.

Complete stable baseline: downloaded 0.28.0 wheel verified against PyPI SHA256, imported from case-local .stable-sdk with the host Hyper dependency. Build and full static/numerical verifier pass; no SDK capability gap identified. Source 0.29.0a3 also passes. Earlier missing-Hyper attempt remains recorded separately.

Static gate result: evidence/case-static-gates.json passes all case-level gates. Full scripts/validate_iteration.py reaches the final global catalogue and fails on the missing output of concurrent 2023-02-23-ww08 comet-chart case; evidence/static-validation.txt preserves the actual failure. Indexes and unrelated cases were not edited. Temporary stable package sources were retained with .snapshot suffix after the package test, so the recursive public-boundary scanner does not mistake SDK implementation for case builder code; the ignored wheel cache and verified PyPI digest support reproducing the package baseline.
