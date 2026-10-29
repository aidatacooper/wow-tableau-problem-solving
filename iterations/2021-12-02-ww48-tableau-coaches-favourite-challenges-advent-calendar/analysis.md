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

## Independent-review correction and implemented workaround

The initial conclusion that the published SDK could not author a mapped image was too broad. The old synthetic probe tested only Cartesian `configure_chart(map_layers=...)`, which ignores the payload. It did not test exported `convert_workbook` / `read_workbook`. Prior reports and frozen artifacts remain byte-identical historical records; `evidence/background-workaround.md` supersedes their capability interpretation.

The released 0.29.0a2 public native-JSON route now authors the background. First the builder independently constructs its own workbook from blank using public semantic APIs. It converts that newly generated workbook to native JSON, inserts an independently specified mapped-image under its datasource, appends the extracted PNG as a hashed resource, and converts back to TWBX. No author workbook, XML or JSON is read or copied. The mapping uses Y horizontal 0–4 and X vertical 0–6; the existing fixed viewport remains 0–4 by 0–7. The background and ornaments are in the same worksheet; there is no dashboard image workaround.

This is explicitly a **structural public-API workaround**, not a dedicated semantic-API pass. `cwtwb_result` is `workaround`; no blocking SDK change is needed. The verifier validates numeric field identity/types, bounds, resource references and exact bytes, then roundtrips the new artifact through the public APIs and repeats XSD and semantic contracts. Focused mutations cover broken image mappings/resources and the reference, filter, tooltip, action and size-direction gaps identified by independent review. A static highlight contract is not evidence of no-grey behavior at runtime.

## Parent gates and acceptable differences

Parent owns independent review and Desktop/Cloud runs. All required features are now locally authored, including the native mapped background. Rebuild and rerun static checks before freezing new evidence if any changes are needed. Desktop must report LOADED; UNKNOWN is failure. Inspect actual tree/image coordinate alignment, star/bauble size, gradient continuity, four year counts, labels, URL payload, filter/select/clear and no-grey behavior. Font/padding differences may be acceptable; missing background or incorrect actions are not. No runtime, visual match, or live events are claimed here.
