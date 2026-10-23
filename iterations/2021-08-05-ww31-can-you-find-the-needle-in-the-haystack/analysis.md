# 2021 Week 31 — Can You Find the Needle in the Haystack?

- **Article**: https://donnacoles.home.blog/2021/08/05/can-you-find-the-needle-in-the-haystack/
  (published 2021-08-05, by Donna Coles)
- **Official challenge**: https://www.workout-wednesday.com/2021w31tab/
  (2021 Week 31, set by Candra McRae, published 2021-08-03)
- **Author workbook**: `2021_08_04_WW31_Unprofitable_High_Sales.twbx`
  (Tableau Public, `rev=1.1`)
- **Dataset**: Superstore for Tableau 2021.2 (9,994 rows, 6 columns after the
  author's extract: Customer ID, Category, Sub-Category, Product Name, Sales,
  Profit)

## The business question

A stakeholder wants a shortlist of products to focus on for improvement. The
conditions are layered, and the brief deliberately forces the analyst away from
hand-written `AND`/`OR` logic:

> Highlight the products that are among the Top 50 for sales, are unprofitable,
> and have a lower than average customer count.

Candra's stated intent is that the solution be built with **sets**, and the
brief constrains the implementation:

| Requirement | Meaning |
| --- | --- |
| **Only one field can be used to filter data** | a single field on the Filter shelf |
| **No table calculations** | only row-level / LoD expressions |
| Product, Category, Sub-Category in the same column, same row | one text block, not three columns |
| Dashboard size 800×650 | fixed dashboard |
| Bars coloured by higher/lower than the dataset average customer count | two-colour categorical palette |
| Same formatting and tooltips | $k formats, custom tooltip |

## How the author solved it

Donna's article walks through building the data out in tabular form first, then
the set-based viz. The logic chain, read off the author workbook:

1. `Customer Count Per Product` = `{FIXED [Product Name] : COUNTD([Customer ID])}`
2. `Count Products` = `{FIXED : COUNTD([Product Name])}`
3. `Avg Overall Customer Count` =
   `{FIXED: SUM([Customer Count Per Product])} / [Count Products]`
4. `Higher than Avg Customer Count` =
   `AVG([Customer Count Per Product]) > SUM([Avg Overall Customer Count])`
5. Set **Top 50 Sales by Product** — top 50 `Product Name` by `SUM(Sales)`
6. Set **Unprofitable Products** — `Product Name` where `SUM(Profit) < 0`
7. Set **Products to Include** — a *combined* set: `intersection` of (5) and (6)

Only (7) goes on the Filter shelf. The `Data` sheet is the author's scratch
table used to verify the components; `Chart` is the published viz.

### The chart

`Chart` is a fake bar chart, not a normal bar chart:

- **Rows**: `Product Name` (header hidden, cell height 51)
- **Columns**: `MIN(1) + SUM(Sales)` — two panes on one continuous axis pair
- **Pane 1** (`MIN(1)`): a `Bar` mark sized to nothing
  (`size = 0.01`, `mark-transparency = 0`), whose only job is to carry a
  `<customized-label>` with `Product Name` on line 1 and
  `Sub-Category | Category` in grey on line 2. The `MIN(1)` axis is pinned to a
  fixed `0..2` range so the invisible bar occupies a stable left column.
- **Pane 2** (`SUM(Sales)`): the real bar, coloured by
  `Higher than Avg Customer Count`, with `Sales` as the mark label and a custom
  tooltip carrying `Product Name`, `Sales`, `Profit`, `Profit Ratio` and
  `# of Distinct Customers`.
- `Product Name` sorted descending by `SUM(Sales)`; gridlines, zerolines,
  borders, dividers, field labels and axis displays all off.
- Palette: `true` → `#c8d0d9` (grey), `false` → `#f7c480` (orange).
  Note the naming trap: "Higher" is grey in the author's legend and "Lower" is
  orange, so a *lower* customer count is the highlighted (orange) case.

## The answer

13 products satisfy all three conditions. Verified independently from the
locked extract (`verify_replication.py`):

| Product | Sub-Category | Sales | Profit | Distinct customers |
| --- | --- | ---: | ---: | ---: |
| Cisco TelePresence System EX90 Videoconferencing Unit | Machines | 22,638.48 | −1,811.08 | 1 |
| GBC DocuBind P400 Electric Binding System | Binders | 17,965.07 | −1,878.17 | 6 |
| High Speed Automatic Electric Letter Opener | Supplies | 17,030.31 | −262.00 | 3 |
| Lexmark MX611dhe Monochrome Laser Printer | Machines | 16,829.90 | −4,589.97 | 4 |
| Martin Yale Chadless Opener Electric Letter Opener | Supplies | 16,656.20 | −1,299.18 | 6 |
| Riverside Palais Royal Lawyers Bookcase, Royale Cherry Finish | Bookcases | 15,610.97 | −669.54 | 5 |
| Bretford Rectangular Conference Table Tops | Tables | 12,995.29 | −327.23 | 11 |
| Cubify CubeX 3D Printer Double Head Print | Machines | 11,099.96 | −8,879.97 | 3 |
| Chromcraft Bull-Nose Wood Oval Conference Tables & Bases | Tables | 9,917.64 | −2,876.12 | 5 |
| Bush Advantage Collection Racetrack Conference Table | Tables | 9,544.73 | −1,934.40 | 7 |
| Tennsco Single-Tier Lockers | Storage | 9,158.30 | −825.75 | 8 |
| Chromcraft Round Conference Tables | Tables | 8,209.06 | −189.98 | 13 |
| Cubify CubeX 3D Printer Triple Head Print | Machines | 7,999.98 | −3,839.99 | 1 |

Key computed values:

- products: **1,849**; total rows: **9,994**
- average distinct customers per product: **5.37642**
- top-50 sales threshold: **$7,699.89** (51st = $7,699.72)
- unprofitable products: **301**
- top 50 ∩ unprofitable: **13** — matching the article's "13 Products"
- below average within those 13: **8** (so 5 of the 13 are above average and
  render grey, which is exactly what the author's screenshot shows)

The brief's prose says "have a lower than average customer count", but the
author's own viz keeps all 13 and only *colours* them by the comparison. The
replica follows the author's viz: the filter is the 13-product intersection and
the average comparison is the colour encoding. This is recorded in `notes`.

## Replication approach

Built with `cwtwb` 0.29.0a1 (`23b1df0`), public APIs only:

```python
editor.set_hyper_connection(hyper, table_name="Extract")
editor.add_calculated_field(...)          # the four FIXED LoD fields + MIN(1)
editor.add_set("Top 50 Sales by Product", "Product Name",
               basis_field="Sales", aggregation="Sum", top_n=50, direction="DESC")
editor.add_set("Unprofitable Products", "Product Name", members=<301 names>)
editor.add_calculated_field("Products to Include",
                            "[Top 50 Sales by Product] AND [Unprofitable Products]",
                            datatype="boolean", role="dimension")
editor.configure_layered_chart("Chart", columns=["MIN(1)", "SUM(Sales)"],
                               rows=["Product Name"], axis_shelf="columns",
                               fold_axes=False, filters=[...], panes=[...])
```

### Workaround: no native set intersection

`cwtwb` exposes `add_set` (top-N, explicit members, all-members) and
`add_combined_set`, but the latter only authors a **union**
(`groupfilter function="union"`). The author's `Products to Include` is an
`intersection`. Rather than emit raw XML, the replica expresses the same
intersection as a boolean calculation over the two native sets:

```
[Top 50 Sales by Product] AND [Unprofitable Products]
```

Both sets stay dynamic (the top-50 set re-ranks against the live extract), and
the view still has exactly one filter field, which is the constraint the brief
cares about. `cwtwb_result` is therefore `workaround`, not `pass`.

The explicit member list for `Unprofitable Products` is computed from the
locked Hyper extract inside the builder rather than hard-coded, so it stays
derived from data the phase boundary allows.

## Phase boundary

The builder reads only `inputs/*.hyper` and writes
`outputs/replicated-workbook.twbx`. It never opens, unzips or imports the
author `.twbx`; the author workbook was opened during analysis only.
