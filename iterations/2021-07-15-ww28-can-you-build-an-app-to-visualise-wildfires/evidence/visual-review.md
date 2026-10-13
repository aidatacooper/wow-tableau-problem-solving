# WW28 Cloud acceptance — can you build an app to visualise wildfires?

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Josh Jackson, built by Donna Coles) is a parameter-driven map: the
user types a latitude/longitude and an acreage, and a buffer sized to that many
acres is drawn around the point so the fire's scale can be compared to a place
you know.

## What was checked

- **Data**: the extract is five dummy rows; the verifier confirms the count and
  recomputes the acreage-to-radius conversion independently
  (5000 acres → 8,326.34 ft radius).
- **Parameters**: `pLocation` (list with location aliases), `pLatitude`,
  `pLongtitude`, `Acres` (5000) and `pZoom` (list 1/2/5/10/50/500) with the
  author's defaults.
- **Geography**: `Location = MAKEPOINT(...)`, `Acres to Feet =
  SQRT(([Acres]*43560)/PI())`, `Fire Size` and `Zoom` are the BUFFER chain.
- **Map layers**: the map has the pale-red fire layer plus the transparent inert
  zoom ring, each with its own Detail field, on the dark base map at 15% washout.
- **Apply button**: the Apply sheet labels 'Apply' and carries both location
  coordinates on Detail.
- **Location case**: the four locations map to the article's coordinates.
- **Actions**: Set Lat / Set Long parameter actions plus a True→False filter
  action.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The base-map layer selection differs slightly; the dark style at 15% washout is
  preserved.

## Workarounds recorded

- A native buffer layer without a Detail field does not resolve its geometry, so
  the map stays at world scale instead of zooming to the buffer. Each buffer
  layer carries its own Detail field, as the author's workbook does.

## Not claimed

This is not a pixel match, and no browser interaction is claimed. The author's
published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification and the native contracts.
