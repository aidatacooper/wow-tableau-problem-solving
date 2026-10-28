# WW44 — Top and bottom profit performers

## Identity and evidence

- Article: https://donnacoles.home.blog/2021/11/04/can-you-show-the-top-and-bottom-profit-performers-for-the-selected-time-period/
- Official challenge: https://www.workout-wednesday.com/wow2021w44tab/ — explicit WOW2021 W44. Official publication date 2021-11-02 was verified by the parent; article publication date is 2021-11-04. The intake tool's null year/week is not used to invent a different identity.
- Author: Donna Coles, `2021_11_03_Top_and_Bottom_Performers`, analyzed from the original repository archive. Article and workbook hashes are recorded in metadata/source-lock.
- Only the packaged Hyper was extracted, once, with `prepare_case.py`. The builder never reads the author archive, XML, article, screenshots, or verifier outputs.
- The matching archive PNG is a Tableau loading placeholder. Subsequent current-hash Cloud author/replica captures now provide valid Month, Quarter and Year references; see evidence/cloud-verification.json and evidence/independent-review.md.

## Business question

Which subcategories contribute most and least to profit in the latest calendar month, quarter, or year? A user selects one of three profit KPI marks to change the comparison without a dropdown. The chart keeps the top five and bottom five visible individually and summarizes the remaining seven as one average, so a large combined middle group cannot misleadingly appear to outperform every individual category.

The official brief specifies two sheets, 700 x 800 pixels, no tooltips, labels hugging the bars, and periods anchored to the maximum data date. The article clarifies the seven-member mean, the two top/bottom sets, and selection retention. Functional correctness and interaction correctness take precedence over typography.

## Raw inputs and period definition

`Orders (Sample - Superstore).hyper` contains `Extract.Extract`: 9,994 rows, with only Order Date (date), Sub-Category (text), and Profit (double). There are 17 subcategories. Earliest date: 2018-01-03. Latest: 2021-12-30. No external data is needed.

The global FIXED calculation computes the latest month, 2021-12-01. Profit is included conditionally by calendar period, rather than by a worksheet date filter:

| Period | Included dates in this extract | KPI profit | Everyone Else mean |
|---|---|---:|---:|
| Month | 2021-12-01 through 2021-12-30 | 8,483.3468 | 422.0875857143 |
| Quarter | 2021-10-01 through 2021-12-30 | 27,448.7260 | 1,243.2569857143 |
| Year | 2021-01-01 through 2021-12-30 | 93,439.2696 | 4,603.3694285714 |

These are neither trailing 30/90/365-day windows nor the entire four-year extract. The quarter containing December is Q4. Dates outside each period yield NULL for that period's profit, not zero. KPIs show currency with zero decimals but all ranking and averaging uses unrounded values. The synthetic calendar test moves the last date to 2023-05-15 and expects May, Q2, and 2023 sums of 5, 9, and 15, respectively.

## Ranking, grouping, ties and filtering order

1. Retain all source rows and all 17 dimension members. There are no datasource, context, category, or worksheet date filters in this case.
2. Calculate the global latest month with a FIXED LOD.
3. Period selects conditional row profit (Month, Quarter, Year).
4. Native sets independently select top five and bottom five records ordered by SUM(selected profit) descending. The bottom set selects the bottom tail of that same descending ordering.
5. A display category keeps an individual name for either set, and otherwise becomes Everyone Else. Color uses Top 5, Bottom 5, or Everything Else.
6. At that grouped level, size is SUM(selected profit) / COUNTD(Sub-Category). Individual bars have denominator 1, the middle bar denominator 7. Retaining out-of-period rows is important to the dimension domain and denominator.
7. Sort the resulting eleven bars by average profit descending, allowing the middle bar to occupy its numerical position.

| Period | Top five (highest first) | Bottom five (higher to lower within bottom tail) |
|---|---|---|
| Month | Copiers, Chairs, Paper, Phones, Storage | Fasteners, Machines, Bookcases, Tables, Binders |
| Quarter | Copiers, Phones, Accessories, Paper, Storage | Supplies, Bookcases, Binders, Machines, Tables |
| Year | Copiers, Accessories, Phones, Paper, Appliances | Fasteners, Bookcases, Supplies, Machines, Tables |

Bottom five is a relative rank, not a negative-profit filter. Positive low performers remain in the bottom group. The raw oracle confirms 17 distinct unrounded profits in each of the three periods, including strict separation at both cutoff boundaries. Exact profits, all seven middle members, and cutoff differences are recorded in `evidence/local-verification.json`.

The author's native sets specify count=5, units=records, without a secondary tie key. The replica preserves this contract. It does not substitute RANK_DENSE <= 5 or invent alphabetical membership as an author requirement. Synthetic tied cutoffs illustrate why dense rank can include six members. Native Tableau selection among boundary-tied members is not verified here; for a changed dataset with ties the verifier deliberately requests review. The oracle uses a secondary name key only to make its no-tie sort reproducible.

## Workbook and interaction design

The workbook starts empty. Public APIs connect the locked Hyper, define one Period string parameter (Month default), calculations and native ranked sets, and create exactly two sheets:

- Period KPIs: Measure Names on columns and three measure values on text. All three amounts stay visible for every parameter value. A label combines the period name and its total.
- Profit Performers: Display Category on rows, two synchronized, folded MIN(Zero) axes, GanttBar marks sized by Average Profit, colored by Performance Group, and sorted descending. Left labels show a negative profit or a nonnegative category name. Right labels show a nonnegative profit or a negative category name. Zero follows the nonnegative branch.

An on-select parameter action sends the KPI's virtual Measure Names to Period with ATTR aggregation. Clear selection is explicitly do-nothing, preserving the last period. Multiple different KPI selections do not imply an arbitrary valid single period under ATTR; parent should inspect live behavior. There is no filter action that would remove the middle seven categories. Both sheets disable tooltips.

## Baseline and differences

Tested release: cwtwb **0.29.0a1**, commit **23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c**. Every build/check process sets PYTHONPATH and CWTWB_SRC to `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src`. The broken global editable install is untouched. a2 was not used. No SDK edits, XML patching, workbook imports, precomputed rank data, or local API workarounds are required. The a1 local result is pass; this does not imply Desktop acceptance.

The replica uses declarative layered Gantt panes instead of copying the author's dual-axis XML. Period is constrained to the three intended selections instead of being an unrestricted string. Title, footer, colors, fonts, and spacing are newly authored. Independent review of the current Month/Quarter/Year Cloud PNGs confirms readable eleven-row endpoint labels, palette and spacing. Selection highlighting and live interactions remain unverified. The official dashboard dimensions, sheet count, period calculations, set semantics, average denominator and action intent are retained.

## Local verification and limits

`verify_replication.py` does not import builder formulas. It independently reads raw rows, computes calendar boundaries in Python, uses math.fsum for category totals, and builds expected memberships and means. Separately, a restricted fail-closed parser translates formulas read from the GENERATED TWB to Hyper SQL. It evaluates all three period scenarios, seven label/value outputs per bar, all nine parameter/KPI combinations, and a shifted-date fixture. The parser supports only the actual expression subset; it does not claim to be Tableau's runtime. ATTR is evaluated as MIN only at the verified single-category display grain.

The verifier checks package/data hashes, relative connections, actual shelf/encoding references, native set definitions, no pre-ranking filters, action mappings, cleared-selection settings, dimensions, sorting, and tooltip configuration. Three intentional mutations (wrong period, wrong averaging denominator, wrong bottom tail) must be rejected. This is local numerical/structural evidence, not a screenshot or live click test.

`case.yaml` remains functional_status=partial and verification_status=pending. visual_status=acceptable_delta is limited to the independently reviewed, current-hash Month/Quarter/Year REST images. The independent raw-input SQL confirms all displayed figures; REST parameter injection does not prove live KPI clicks, clear selection, multi-selection or hover. Parent subsequently supplied exact-hash Desktop LOADED and corpus LOADED=50 FAIL=0 UNKNOWN=0 evidence, plus nine current-hash REST CSV records. Only live KPI click/clear/multi-selection/hover events remain unverified. Final delivery regenerated the shared catalogue and reran repository tests; current outcomes are in `evidence/local-gates.json`, with initial baseline outcomes preserved under `evidence/baseline-a1/`.

## Reproduction and freeze

From the isolated checkout in PowerShell:

```powershell
$env:PYTHONPATH='C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0/src'
$env:CWTWB_SRC=$env:PYTHONPATH
$env:PYTHONUTF8='1'
python -X utf8 iterations/2021-11-04-ww44-can-you-show-the-top-and-bottom-profit-performers-for-the-selected-time-period/build_replication.py
python -X utf8 iterations/2021-11-04-ww44-can-you-show-the-top-and-bottom-profit-performers-for-the-selected-time-period/verify_replication.py
python -X utf8 scripts/validate_iteration.py iterations/2021-11-04-ww44-can-you-show-the-top-and-bottom-profit-performers-for-the-selected-time-period
```

The full validator rebuilds and can change artifact UUIDs. After freezing, run full validation only against an isolated case/lab copy; metadata-only validation is safe against the delivered case. The final artifact's SHA256 and parent commands are recorded in `evidence/handoff.json`; any subsequent real rebuild requires a new hash and new runtime evidence binding. Final delivery preserved the frozen current hash. The prior baseline workbook is archived at `outputs/baseline-a1-replicated-workbook.twbx`; its original evidence paths are historical.
