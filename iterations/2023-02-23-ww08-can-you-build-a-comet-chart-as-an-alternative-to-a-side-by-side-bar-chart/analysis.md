# Analysis: 2023 Week 08 comet chart

## Identity and selection

Article: https://donnacoles.home.blog/2023/02/23/can-you-build-a-comet-chart-as-an-alternative-to-a-side-by-side-bar-chart/
Official: https://www.workout-wednesday.com/wow2022w08/ (legacy slug; API title/date identify **2023**, published 2023-02-22).
Full official requirements were saved in evidence/official.json. Intake was run against the local article/link catalogue and live official API. origin/main was freshly fetched at e32c8151a8c596c082763007d2ec5fc83cf1ddff; its iteration inventory has no ww08 2023 case. Local active 2023 cases were ww14 and ww48. GitHub open issue list returned []. Other agents own 2024/2025.

## Business question and complete standard requirements

Compare 2021 and 2022 sales across all 17 Superstore sub-categories with less scanning than side-by-side bars. The selected tier is the official standard LOD solution. The separately marked optional ADVANCED task (table calculations only) is not claimed. All standard requirements remain included:

1. 800 x 700 dashboard and exactly one worksheet.
2. One comet per sub-category: narrow end 2021, wide end 2022, even when sales decrease.
3. Labels show the 2022 sales, with whole-number formatting; order by latest sales descending.
4. Match the white circle inside the wide end, and the increasing year size legend.
5. Red represents falling sales; remaining comets are warm grey.
6. Match formatting: light grey background, row separators, no visible quantitative axes/grid/zero lines, title, legend and credit footer.
7. Preserve year/sub-category/sales hover details from the reference. No parameter or filter action is needed for the base challenge.

## Analysis boundary and reconstruction

The author TWBX was opened only during analysis. prepare_case extracted its packaged Hyper and recorded SHA256 in inputs/source-lock.json. No author XML/template is copied into the builder. The input has 10,194 rows and five source columns. Builder starts TWBEditor("") and uses public connection, calculated-field, layered-chart, style, tooltip, dashboard and window methods only. It does not read analysis evidence, screenshots, expected totals or author files.

LOD fields calculate 2022 and 2021 sales for each Sub-Category; MIN(Latest Sales) places the white circle without multiplying the repeated LOD value. The line's Sales remains SUM at Sub-Category/year grain. YEAR(Order Date) drives both ascending path and width, and a native year filter includes exactly 2021/2022. A second ordinal year field drives circle size and the native size legend. A synchronized folded columns axis overlays the circle on the line. Native line-end labels suppress the first year and retain the last year. A computed descending latest-sales sort preserves rank; the 110% transparent percentage band leaves label room.

The official dataset ends in 2022, so explicit 2021/2022 LODs implement the required comparison. The author used the equivalent maximum-year LOD. No data scaffolding, preaggregated display values or embedded author calculations are imported.

The author PNG originally stored in dashboards is a Tableau loading placeholder. The actual article reference image was downloaded to evidence/author-reference.png from https://donnacoles.home.blog/wp-content/uploads/2023/02/image-57.png and visually inspected. It shows the expected 17 rows, labels, red Machines/Envelopes and grey remaining comets.

## Numeric acceptance

Analysis-stage SQL GROUP BY produced evidence/expected-sales.json. The verifier separately sums the 10,194 source rows with Python Decimal and compares all 34 annual totals at tolerance 0.00001. The packaged Hyper hash must equal the locked extracted source hash. 2021 total: 613,933.58; 2022 total: 745,567.5312. Only Machines (55,906.886 -> 43,887.875) and Envelopes (4,745.41 -> 3,378.574) decline. Phones leads at 105,668.392 and Envelopes is last. These values match all 17 whole-number labels visible in the reference image.

This checks source arithmetic and emitted contracts, not Tableau query execution. Parent must confirm rendered labels and hover values on the final artifact using evidence/desktop-acceptance.md.

## SDK provenance and limitations

Latest PyPI stable queried 2026-11-14 is 0.28.0. Its wheel digest and actual target-package import path are in evidence/stable-run.json; it passes the complete builder and automatic verifier. The local prerelease source is explicitly selected with CWTWB_SRC and PYTHONPATH both C:/Users/imgwho/Desktop/project/cwtwb/src. Actual version, complete Git SHA, dirty status, source-file hashes, source-tree digest and dirty diff are captured in evidence/final-run.json, sdk-source-manifest.json and sdk-source.diff. Stable and final evidence are separate and preserved. No SDK modification was made for this case; no reusable capability gap identified, no SDK issue/PR created.

Static checks cannot certify circle sizing, line-end label visibility, tooltip hit targets or worksheet fitting. Those remain explicit manual requirements. Functional status stays partial and visual status not_evaluated until the parent completes serialized Desktop/load, rendered numeric and visual/tooltip checks with evidence bound to the final artifact hash. The whole repository regression corpus is also the parent's integration responsibility.

Final source settled during the publishing task: clean checkout 2b72232245959934281c49308f5c3b2fca8fc519, version 0.29.0a3, source tree digest 491d5979516636ea43779ed3205aed724c9e19e4f4f1c3558c2877ff43910d8c. The final full validator rebuilt the artifact and passed all case-specific gates; its final shared-catalogue freshness gate failed as expected while parent-owned indexes await integration. Repository unittest discovery: 83 run, 81 pass, two failures solely from the same catalogue freshness check. No unrelated file was edited to resolve these integration gates.
