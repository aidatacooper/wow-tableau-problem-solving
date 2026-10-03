# Beautiful dynamic bar chart, 2020 WW02

Donna's article is dated 2020-01-11. The official challenge post 3354 was
published on 2020-01-07. This is the next unconsumed challenge after WW01.
The source filename correctly says WW02, while its dashboard says WW01;
the original dashboard name is preserved rather than silently corrected.

The question is how Sales, Profit Ratio, and Items Per Order vary across
the last twelve months, thirteen weeks, or fourteen days. A fixed Today
parameter is 2020-01-01 because Superstore ends in December 2019. Sales
is SUM(Sales), Profit Ratio is SUM(Profit)/SUM(Sales), and Items Per Order
is SUM(Quantity)/COUNTD(Order ID). These are recomputed within each
selected period, rather than averaging preaggregated ratios.

The reference has two worksheets, Chart and Selector, on a 1100 x 800
dashboard. Selector drives the spaced Selected Measure string values via
a select parameter action sourced from Tableau's virtual Measure Names.
A True-to-False filter action deselects the source, with show-all clearing.
Date Period is a visible dropdown. The replica starts from TWBEditor("")
and only reads the extracted, locked Hyper. Original TWB/TWBX and downloaded
HTML are analysis-only, absent from the builder and submitted source.

The date filter uses the original inclusive cutoff, not a fixed number of
complete calendar periods. Week truncation starts Sunday. This yields
12 monthly buckets, 14 weekly buckets (including a partial opening week),
and 13 daily buckets because one day in the fourteen-day window has no
orders. Empty days are not fabricated. All nine metric/time combinations
are verified with independent fact-level Python aggregation.

Sales labels use REGEXP_REPLACE to insert thousands separators into rounded
dollar amounts, meeting the official regex formatting requirement. Profit
Ratio and Items Per Order use separate conditional label fields formatted
to one decimal; only the active field contains a value. Sales is purple
#9264a5, Profit Ratio green #86b35e, Items Per Order cyan #63ccc6. Month
headers use short month and two-digit year, weeks use Week plus number,
days use month/day. Selector text uses filled/open circle glyphs with
the selected metric, a documented small difference from author shape marks.

The generic independent-axis and Measure Names action enhancements from
WW01 are reused. Cloud review also exposed that the existing parameter-control
`show_title=False` option was ignored; the generic layout renderer now forwards
that option, with synthetic regression coverage. The dynamic dashboard title
uses parameter-bound rich text. The selector uses three glyph labels; despite
per-pane color styling, captured Cloud labels render dark gray, as recorded
in the visual review. Acceptance is Cloud REST images/data states plus artifact source/target/event/clear
contracts. No actual browser clicks or hovers are claimed. Chart CSV
covers dated bar marks; Selector CSV does not establish metric correctness.
