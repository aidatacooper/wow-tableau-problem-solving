# Visual review

The final Cloud dashboard shows all 17 Sub-Categories ordered by descending
longest streak, grey stepped monthly sales, green circles on all tied streak
endpoints, and a 0-5 legend. Native independent axes preserve each row's scale.
The leading rows are Appliances, Bookcases, Phones (5) and Art (4), matching
the author. All 4,896 exported month/category/measure cells agree with the
original author, including null sales in 34 missing category-months.

Accepted deltas: all rows fit in one dashboard rather than an initial scroll
viewport, Sort's negative grouping header remains visible, lines/circles and
legend are smaller, alternating row shading and min/max labels are absent.
Custom tooltips retain category and sales, while the axis supplies month.
No browser interactions are required by this static chart.

Result: acceptable_delta. Calendar scaffolding introduces only null-sales rows
for missing months; the streak chain remains native PREVIOUS_VALUE/WINDOW_MAX.
