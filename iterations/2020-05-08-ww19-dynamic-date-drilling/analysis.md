# WW19 dynamic date drilldown

Article 2020-05-08; official Week 19 challenge 2020-05-05, WordPress 3657. The locked extract has 3,312 2019 sales records. Build reads only extracted Hyper and public SDK APIs, never the source workbook.

The native datetime set stores the author's three selected dates (November 2, 3 and 6). A select set action assigns marks and keeps values when clearing; a second select action changes Drill Down to one. Dates then aggregate by day within inclusive Sunday/Saturday boundaries of the earliest/latest selected weeks. The reset worksheet changes the parameter to zero while leaving stored set values unchanged. Weekly default intentionally matches the author's exclusion of the last partial week: first Sunday December 30, 2018 through Saturday December 28, 2019.

REST default/daily/reset parameter states cover 52 weekly marks, 14 daily marks and restored 52 marks. All chart sales, total and average values are independently recomputed. Additional single-week, disjoint-week, single-day and multiple-day interval scenarios are independently simulated and checked against native calculation/action contracts; REST does not mutate the selected set, and no browser clicks are claimed. Average reference lines and conditional reset visibility are native workbook contracts. Images remain required before visual acceptance.
