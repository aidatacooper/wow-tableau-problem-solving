# Advent calendar analysis

## Identity and question

Article published 2021-12-02; canonical challenge 2021 week 48. The official WordPress API reports post 6459 published **2021-11-30T21:43:49** (site calendar date, no timezone conversion). The author workbook filename `2021_01_12_WW48_Advent_Calendar.twbx` contains a real date typo; its view is `2021_12_01_WW48_Advent_Calendar`. Neither filename determines challenge date.

The reader explores coaches' 24 favourite challenges, sees their distribution across years, filters the ornaments by year, and opens a chosen challenge. This is a static countdown calendar, NOT a TODAY()-gated calendar: all days 1–24 are available. Null Day is the Christmas Day star, with no challenge URL.

Official source: https://www.workout-wednesday.com/tab2021w48/
Article: https://donnacoles.home.blog/2021/12/02/tableau-coaches-favourite-challenges-advent-calendar/

## Author analysis (completed before construction)

The package contains two Hyper extracts, one tree image, and two base64-embedded custom shapes. All were extracted for analysis; the builder never opens the author package or XML. The first Hyper has 25 rows: 24 challenge records and a star at X=6/Y=2. The second has 25 year records and Range endpoints 1/500 for Tableau densification. Counts are 2018=10, 2019=3, 2020=5, 2021=6. X is vertical and Y horizontal, despite their names.

Tree: coordinates Y on columns, X on rows; mark grain one Day/URL; Day label white/bold/center; null Day chooses a larger star. Image mapping is horizontal 0–4 and vertical 0–6; viewport horizontal 0–4 and vertical 0–7. The fixed viewport must survive year filtering. Tooltips distinguish Christmas Day, 1 day, and plural days. No map navigation controls are needed. The image MUST reside in the same worksheet as the ornaments; a dashboard image is explicitly disallowed by the official challenge.

Bar: four ascending years, counts at bar ends, red/green gradient within bars, year/count tooltip. Author uses densification, INDEX(), TOTAL(COUNT(...)), WINDOW_MAX(range), and a transparent count overlay. A 1000×800 dashboard places the tree on the left and bars lower right, with title, click instructions and credits. There is no required color/shape legend: these encode decoration, not a quantitative measure requiring interpretation.

Interactions: Bar select filters Tree by Year, multiselect unions years, clear restores 25 marks. A selected year excludes the null-year star, matching the author behavior. Tree select opens that mark's URL, with no greying of other ornaments. The builder adds a constant-field self-highlight action alongside the URL action. No URL was executed during implementation. Parent should inspect URL payloads without navigation unless explicitly authorized to test external opening.

## Independent construction and oracle

Blank `TWBEditor('')`, public SDK methods only. Original data files remain byte-identical and source-locked. `gradient.csv` materializes 500 segments per year; widths sum exactly (within floating-point tolerance) to the raw number of challenges. `gradient.hyper` is its typed representation. `calendar.hyper` unions the 25 unchanged tree rows with 2000 segment rows and a Kind discriminator. Both sheets share this datasource, avoiding ambiguous cross-datasource action mappings. Fixed Kind filters separate the two grains. No table calculations or author XML are imported.

A Gantt segment begins at `(segment-1)*count/500`, has width `count/500`, and gradient value `(500-segment)*count/500`. A synchronized transparent Bar layer labels `AVG(Challenge Count)`; SUM would incorrectly multiply the total by 500. Explicit shelves bind both layers. The independent verifier queries raw Hyper rows, corroborates counts with the second extract, verifies every segment cell and all 2025 runtime rows, checks emitted expressions/dependencies/actions/assets, and rejects negative mutations. This proves static/data behavior only, not Tableau's rendering or live event execution.

## Reproduced blocker

Neither published cwtwb 0.29.0a2 nor merged cac8820f26e703c3858253adfa21efd989eb8a78 offers a public coordinate-mapped raster image primitive. `probe_background.py` uses synthetic coordinates and a synthetic PNG, not author materials. Existing `configure_chart(map_layers=...)` on a Cartesian chart accepts the layer request but silently emits no mapped-image and packages no PNG. Public chart/layer/style/shape APIs and capability registry were inspected; the only `mapped-images` implementation occurrence is schema ordering, not construction. Geographic map layers do not bind a local raster to arbitrary Cartesian fields. Shape assets embed a mark image, but provide no independent four-edge image mapping; using an approximate pixel-sized shape would not establish the required fixed 0–4/0–6 coordinate contract.

The maximal working artifact includes ornaments/star, labels/tooltips, fixed axes, bars, URL/filter/self-highlight actions, layout and help. **It does not contain the tree background.** This is deliberately reported as `functional_status: partial`, `visual_status: not_evaluated`, `cwtwb_result: blocked`. The extracted tree PNG is ready for the missing API. No approximation is passed off as completion. See `evidence/background-blocker.md`.

## Parent gates and acceptable differences

Parent owns the generic SDK capability implementation/review and Desktop/Cloud runs. After adding a supported background-image call, rebuild and rerun static checks before freezing new evidence. Desktop must report LOADED; UNKNOWN is failure. Inspect actual tree/image coordinate alignment, star/bauble size, gradient continuity, four year counts, labels, URL payload, filter/select/clear and no-grey behavior. Font/padding differences may be acceptable; missing background or incorrect actions are not. No runtime, visual match, or live events are claimed here.
