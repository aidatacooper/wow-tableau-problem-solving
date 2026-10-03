# WW22 Profitability polygons

Article date 2020-05-29; official challenge date 2020-05-26 (WordPress post 3699). Scope is author v2 with native additive set action, replacing the earlier dashboard parameter switch.

Compare revenue to budget and customer review per subcategory. Three union copies of eight customer/category observations give 24 locked rows. Use means, not sums. WW/WW1/WW2 map to vertices (0,AVG Review), (20,AVG Revenue/20), (20,AVG Budget/20). Profit = AVG Revenue - AVG Budget; margin = Profit / AVG Budget. Tables -60/-60%, Chairs +50/+166.7%; denominator must remain budget.

Gray Polygon shows all three vertices, and color Line joins review to revenue. Selected Sub-Cats starts empty; selecting adds categories, splitting Expand panes; clearing excludes all and regroups to Click to Expand. Event/source/target/additive/clearing behaviors are verified in artifact. REST query states do not execute clicks. Default and Chairs-filtered screenshots validate data/layout; all 12 groups and five metrics must appear in CSV. Independent raw-data oracle additionally computes all profit/margins.

Builder starts TWBEditor("") using only locked Hyper and public APIs. Author/export workbooks are scratch analysis only. Export visibility changes preserve formulas, data and dashboards.

Generic SDK bug found: selection_mode emits a param instead of direct native add-or-remove-marks. Parent coordinates synthetic fix. Cloud review pending.
