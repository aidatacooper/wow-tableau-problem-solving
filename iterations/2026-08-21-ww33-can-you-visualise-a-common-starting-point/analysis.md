# 2026-08-21 WW33 — common starting point

The article describes a two-chart rocket view of product launches. The current-time chart uses Sunday weeks over the last 52 weeks anchored to 15 August 2026. The normalized chart aligns each product to week zero using `Launch Week = DATE(DATETRUNC('week',{FIXED [Product]:MIN([Date])}))`, then plots `Weeks Since Launch` against daily orders for the first 52 weeks.

The extracted Hyper data contains Date, Product, and Daily Orders for five products (2023–2026). The replica builds Current Time and Common Start worksheets and a dashboard from the extracted data. It preserves product color, labels, tooltips, launch-week normalization, and the 52-week filter. The released cwtwb API supports the required calculated fields and line charts; no reusable SDK gap was found.

Acceptance scenarios:
- Current Time contains only the anchored 52-week window and has one series per Product.
- Common Start places every product at Weeks Since Launch = 0 and excludes values after week 52.
- Recomputing weekly totals directly from the Hyper extract yields non-empty values for all five products.

Visual differences are limited to font, spacing, and decoration. Live hover and filter events were not executed; the case remains partial.
