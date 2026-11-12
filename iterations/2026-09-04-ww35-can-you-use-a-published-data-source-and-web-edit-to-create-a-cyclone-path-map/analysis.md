# 2026-09-04-ww35-can-you-use-a-published-data-source-and-web-edit-to-create-a-cyclone-path-map

## Problem

Build a cyclone path map from the published Historical Tropical Cyclones data source using Tableau Public web authoring. The chart requires storm category, start month, a point map, and a line layer for each storm path.

## Why the obvious approach fails

The author workbook is a thin TWBX that references a published Tableau data source. It contains no packaged Hyper/CSV data, so the independent-input phase boundary cannot be satisfied. `prepare_case.py` correctly stops with `No packaged data file found`.

## Tableau solution chain (analysis of the author workbook and article)

```text
published Historical Tropical Cyclones source
→ Tropical Storm System CASE on Usa Sshs
→ ISO Datetime and Start Date per Storm LOD
→ June/July 2026 + Season 2026 filters
→ map point layer + white line path layer
→ category bar chart + dashboard
```

The author also uses a web edit flow and browser-only published-source connection.

## Required behavior

- Categorise Usa Sshs codes -5..5 into the documented storm-system labels.
- Filter to Season 2026 and June/July 2026 start months.
- Show storm points sized by Usa Wind (Kts) and a line path by Name/ISO Datetime.
- Bar chart counts distinct storm timestamps by category.

## Allowed visual differences

Map basemap, palette, labels, and dashboard geometry can vary after an independent source is supplied.

## cwtwb baseline

Blocked before SDK build: no packaged data file is available, and browser interaction/published-source authentication is outside the local phase boundary. A text-only placeholder workbook is supplied so the iteration remains Desktop-loadable. `browser_interaction_executed=false`.
