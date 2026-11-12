# 2026-08-14 WW32 — sets for top and bottom states/cities

The article uses Tableau sets for Top 5/Top 1 and Bottom 5/Bottom 1 States and Top 5/Bottom 5 Cities. State fill color is driven by the state sets; city marks use separate color, shape, and size calculations. The tooltip reports sales plus counts of top, bottom, and other cities.

The extracted Superstore Hyper data contains Country/Region, City, State/Province, and Sales. The replica computes the documented set membership from independently aggregated extract totals, then exposes State and City worksheets plus a detail table. This keeps the observable ranking behavior deterministic while retaining the article's set-driven calculation chain. The released cwtwb API supports the formulas, charts, and dashboard without a reusable capability gap.

Acceptance scenarios:
- The five highest-sales states are California, New York, Texas, Washington, and Pennsylvania and receive the Top 5 style.
- The five lowest-sales states are North Dakota, Newfoundland and Labrador, Nova Scotia, New Brunswick, and Saskatchewan and receive the Bottom 5 style.
- The five highest-sales cities are New York City, Los Angeles, Seattle, San Francisco, and Philadelphia; city styling fields are present and used by the City worksheet.

Map tiles and native mark-layer interaction were not executed in this environment, so functional status is partial and visual status is acceptable_delta.
