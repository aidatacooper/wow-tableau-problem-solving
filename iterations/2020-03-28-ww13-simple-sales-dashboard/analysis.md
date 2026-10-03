# WW13: sales performance with dynamic date mapping

The dashboard shows ten Sales/Profit KPIs: MTD, previous MTD, month-over-month difference, projected run rate and YTD, plus overlaid prior/current year monthly bars. Runtime TODAY month/day is mapped into the latest data year and reduced by one day. The author workbook currently has maximum order year 2019; October runtime therefore intentionally displays September/October 2019 rather than forcing the original March 2020 screenshot. Author formula TODAY remains unchanged; replica uses equivalent explicit FIXED maximum-year LOD.

The independent oracle reads raw order dates, sales and profits and evaluates date endpoints, previous-month clipping, MTD/PMTD/YTD and run-rate arithmetic separately in Python. Cloud Date worksheet CSV determines the runtime mapped Yesterday without inferring it from KPI totals; it is independently constrained to the capture date and possible one-day site timezone difference. Both workbooks must expose all ten KPI values and all included year/month bars. Original official challenge date March 24 maps to March 23, 2019; this is contextual evidence, not a claim that runtime captures reproduce the original March metrics.

Date, KPI, Sales and Profit are built from scratch; a CHK Data worksheet exposes all ten measures for complete REST data verification. Data export does not prove browser hover behavior. No dashboard actions exist in the author. KPI rich labels and blue/light-blue year overlay are reviewed visually after Cloud capture.


## Layout polish

Public SDK styling preserves calculations and data. Restore the grey main partition with white monthly chart cards, left title and date, and right upper attribution. Cloud recapture is required for the changed workbook hash.
