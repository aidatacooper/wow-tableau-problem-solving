# WW22 paired Cloud review

Result: **acceptable_delta**, reviewed 2026-10-03. This is not a pixel-identical claim.

Replica artifact SHA256: `f1b24f6628d3345341b7ef0f80e4d4f23c23c045b5d761585d37e9e1dcda5c10`.
Author comparison artifact SHA256: `eff40f232ab593fdf03834fa564b43d9f15b007343addc43a59a5488805d820d`.
The Cloud manifest binds both workbooks and every PNG/CSV to these artifacts. No workbook rebuild followed capture.

## Images inspected

Both default PNGs and both Chairs-filter PNGs were inspected side by side. The default view contains all four filled three-vertex polygons: Labels (review 5), Bookcases (3.5), Tables (2.5), and Chairs (1.5). Their review/revenue/budget geometry and overlaps reproduce the source. The Tables revenue line is red and descends; the three profitable lines are gray. The Chairs REST filter leaves one rising gray line and one polygon in both workbooks. The instructional triangle and profitable/non-profitable legend remain visible; the Chairs legend drops the non-profitable entry in both renders.

The complete Profitability title, budget-recovery subtitle, How to read it heading, Avg Review legend label, revenue/budget endpoints, Click to Expand text, category/review labels and footer are visible without truncation. The final refinement removed the earlier clipped title and missing subtitle, and displays review values as 5/3.5/2.5/1.5 rather than padded decimals.

## Independent data and action checks

The verifier independently reads all 24 locked Hyper rows and checks averages, three union-copy coordinates, profit and budget-based margin for all categories. Both default Data exports cover all four categories ? three union copies ? five values (60 each). Both Chairs exports cover one category ? three copies ? five values (15 each). All four CSV files pass against the raw-data oracle, including source/replica hash checks. The source and replica CSV bytes are also identical for each state.

The additive set action, event/source/target, clear behavior, expansion calculation and empty initial membership are checked through the generated artifact. REST filtering demonstrates the declared filtered state; no browser click, hover or actual expansion event was executed or claimed. The Data CSV proves vertex/metric data, not the browser action execution.

## Remaining visual differences

The replica uses less top whitespace: title, instructional section and main chart begin higher than the source. Its main chart is consequently taller while retaining the same normalized vertex geometry. Review labels are centered near the left vertices instead of the source's left alignment, and the source's thin vertical endpoint spines are omitted. Line strokes and review point circles are thinner/smaller, and the instructional diagonal lacks the source's white halo. The two-item legend has smaller dots and faint guide lines. Footer attribution and plain URL typography also differ. These layout/styling deltas are explicit; none removes a category, changes its geometry or obscures required text.
