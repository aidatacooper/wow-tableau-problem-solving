# WW11: Superstore overview using nested layout containers

Article 2026-03-23; official challenge 2026-03-17 (REST post 21463). Independent workbook starts at TWBEditor("") and reads extracted Hyper only.

The author overview uses 12 nested flow containers: base/header/body, equal left/right panes, three outer and inner KPI rows and footer. Three rows show current/prior Sales, Profit and Profit Ratio, change circles and synchronized monthly lines. The right scatter uses current Sales/Profit per Sub-Category, order count size and window averages to assign four quadrants, with mean reference lines.

Orders contains 10,194 records dated 2023-2026; CY is 2026 and PY 2025. Author Hyper also has Returns and People tables, but each worksheet uses Orders fields only. Explicit table_name avoids the SDK default Extract lookup. Ratio fields retain author INCLUDE year/month formulas.

Acceptance covers 10 worksheets, nested flow containers, 12 months per year, both line colors and synchronisation, 17 subcategories, table calculation addressing and mean lines. Dashboard CSV covers one worksheet only; the independent Hyper oracle covers all monthly measures and scatter points. Cloud REST images and actual data comparison are pending and no browser event is claimed.

Source: https://donnacoles.home.blog/2026/03/23/can-you-use-layout-containers/

Author workbook: https://public.tableau.com/views/2026_03_18_WW11_Layout_Containers/WOW2026Week11

Rounded-corner API and raw feature-gated output are required: 5-pixel shadow containers, 20-pixel change indicator zones. Outer light-gray and inner white backgrounds/padding reproduce the author framing; these are built through public corner_radius/style keys.

Author quirk preserved: the Profit Ratio KPI card text says Total Profit CY/PY, despite percentage units. Its actual measure is SUM of monthly INCLUDE ratios (154.8% and 161.2%); it is intentionally not changed to overall profit/sales. Source label spelling is retained to fit the original 140-pixel card.
