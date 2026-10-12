# WW24 Cloud acceptance — can you visualise the Cholera Outbreak?

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Lorna Brown, rebuilt by Donna Coles) recreates John Snow's 1854
cholera map with four native map layers, two ranking bar charts and a
click-a-pump parameter action.

## What was checked

- **Data**: the locked extract has 8 pumps, 489 individual deaths and 250
  aggregated death locations (the 489 deaths roll up exactly into the 250 rows).
- **Distance model**: the verifier re-implements Tableau's WGS84 Vincenty
  `DISTANCE(...,'m')` and recomputes every per-pump average; the eight labels
  match the article's screenshot exactly (119/248/297/335/260/231/421/278 m).
- **Deaths within**: `SUM(INT(distance <= avg))` reproduces 259/242/252/258/
  228/251/256/279.
- **Map layers**: four declared native layers (Heatmap density, BUFFER circle,
  red pump circles, black aggregated-death circles), normal map style at 0
  washout with only streets/highways/routes enabled.
- **Selection**: `pSelectedPump` + `Is Selected Pump?` + the `{FIXED}` selected
  lat/lon/location/average distance and `BUFFER(...)` geometry.
- **Interactivity**: three on-select parameter actions set the pump, and three
  filter actions map True -> False to suppress the selection highlight.

## Accepted visual differences

- Fonts, padding and the exact heatmap kernel size differ; the density blob is
  the same shape and extent.
- The dashboard title is clipped by the Cloud rendering ("1854 Cholera
  Outbreak…") because the text zone is narrower than the author's; the wording
  is identical.
- OpenStreetMap shows a 2026 copyright year rather than 2021.

## Workarounds recorded

- A Heatmap (density) mark is gated behind Tableau's `Heatmap`
  document-format manifest entry. `configure_chart(mark_type="Heatmap")` writes
  the mark class but not the flag, so Desktop refuses the workbook with error
  d2e8da72 even though the XML is schema-valid. The builder calls
  `editor._ensure_manifest_entry("Heatmap")`; the author's workbook carries the
  same entry. A generic SDK fix would map the mark class to its manifest flag
  in the builder's `_reconcile_manifest_flags`.
- The author's three-table 1=1 Hyper relationship returns Cloud error 403132;
  the builder materialises one flat (pump x individual death) Extract instead.
  `DISTANCE` is defined per pair, so the flat grain is equivalent.
- The author uses one parameter action across all three sheets; the released
  SDK's `source_sheets` list is filter/highlight only, so the replica writes one
  parameter action per sheet.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses
the article's written specification, the article's build screenshots and the
native workbook contracts.
