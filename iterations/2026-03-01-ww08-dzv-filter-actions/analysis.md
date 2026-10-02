# WW08: Dynamic visibility and customer filtering

Article 2026-03-01; official challenge 2026-02-26. The official page reused /wow2025w9tab/ but REST post 21377 identifies WOW2026 week 8.

Author data: 9,994 Superstore orders, state/customer/product grain. Main KPI Sales/Profit/Profit Ratio/Quantity follows the selected state. State selection comes from the filled map parameter action. A boolean state-not-empty calculation controls the entire customer panel through a datagraph visibility binding. Customer dropdown shows only relevant customers and omits All. Customer KPI/product rows share a customer filter. Reset sets the state parameter empty and clears both customer filters.

Only extracted Hyper is read by the builder. Original XML was inspected during analysis; public API starts at TWBEditor(""). SDK adds a reusable boolean layout visibility primitive plus relevant-value and All-option control settings. Eight synthetic tests cover graph edges, binding replacement, type validation, roundtrip and MCP layout routing.

Acceptance: verify artifact action sources/targets/events/clear behavior and graph field/zone/UUID edges. Independently aggregate all data, California and Texas and a sample relevant customer per state. Cloud REST images test the default hidden panel and selected visible panel; CSV scope will be determined from actual exported columns. No browser action is claimed.

Source: https://donnacoles.home.blog/2026/03/01/dzv-filter-actions/

Author workbook: https://public.tableau.com/views/2026_02_25_WW08_DMZ_Filters/2026_02_25_WW08_DMZ_Filters

Cloud Customer Name request is global: author and replica both apply it to Main KPI/map as well as customer details. This REST behavior is not evidence of the browser quick filter target scope. The artifact group binds only Customer Orders and KPIs-Customer; reset and visibility events remain verified as serialized contracts.

Reusable public SDK additions: layout visibility graph, parameter text run, selected-worksheet filter linking, explicit geographic role/country, rich Measure Names/Multiple Values labels and explicit measure order.
