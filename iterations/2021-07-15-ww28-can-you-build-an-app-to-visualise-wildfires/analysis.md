# 2021-07-15-ww28-can-you-build-an-app-to-visualise-wildfires

## Problem

Build a small "app": type a latitude/longitude and an acreage, and draw a buffer
sized to that many acres around the point so the fire's scale can be compared to
a place you know. A location list plus an Apply button sets the coordinates.

## Why the obvious approach fails

The "data" is five dummy rows — it exists only so Tableau has something to
connect to. Everything the map draws comes from parameters:

- `Location = MAKEPOINT([pLatitude], [pLongtitude])` gives the centre point.
- `Acres to Feet = SQRT(([Acres]*43560)/PI())` converts the area to a radius,
  because a buffer takes a distance, not an area.
- `Fire Size = BUFFER([Location],[Acres to Feet],'ft')` draws the visible circle.
- `Zoom = BUFFER([Location],[pZoom] * [Acres to Feet],'ft')` draws a larger,
  invisible ring whose only job is to widen the map extent by the zoom factor —
  the visible circle alone would fill the whole view.

The trap is that the invisible zoom ring must still be a real map layer: if it is
omitted the map does not zoom out, and the buffer fills the frame with no
context. It must also be made fully transparent and inert so it never renders or
catches a selection.

## Tableau solution chain

```text
data (5 dummy rows)
→ pLocation (integer list 1-4 with location aliases)
→ pLatitude / pLongtitude (real inputs), Acres (5000), pZoom (list 1..500)
→ Acres to Feet = SQRT(([Acres]*43560)/PI())
→ Location = MAKEPOINT([pLatitude], [pLongtitude])
→ Fire Size = BUFFER([Location],[Acres to Feet],'ft')
→ Zoom = BUFFER([Location],[pZoom] * [Acres to Feet],'ft')
→ Location Lat / Location Long = CASE [pLocation] WHEN n THEN <coords> END
→ Map: two native buffer layers (pale-red fire over the invisible zoom ring)
  on the dark base map at 15% washout
→ Apply sheet: a text 'Apply' mark carrying both location coordinates
→ dashboard: Set Lat / Set Long parameter actions plus the True->False filter
  action that removes the Apply button's selection highlight
```

## Required behavior

- `ww28-parameters`: the location, latitude, longitude, acres and zoom
  parameters exist with the author's defaults and domains.
- `ww28-geography`: `Location`, `Acres to Feet`, `Fire Size` and `Zoom` are the
  MAKEPOINT/SQRT/BUFFER chain, and the acres-to-radius conversion is
  `SQRT((acres*43560)/PI())`.
- `ww28-map-layers`: the map has the visible fire layer and the inert zoom layer,
  with the zoom layer transparent.
- `ww28-apply-button`: the Apply sheet labels 'Apply' and carries both location
  coordinates on Detail.
- `ww28-location-case`: `Location Lat`/`Location Long` map the four locations to
  the article's coordinates.
- `ww28-actions`: two parameter actions set pLatitude/pLongtitude from the Apply
  sheet, plus a True->False filter action.

## Allowed visual differences

- Fonts, padding and the exact stroke widths differ.
- The base-map layer selection differs slightly; the dark style at 15% washout is
  preserved.

## cwtwb baseline

Tested with the released SDK `0.27.1` (`4cd2c61c`).

- `configure_chart(mark_type="Map", map_layer_mode="native",
  map_layers=[...])` builds the two buffer layers. The `detail` field on each
  layer matters: without it the geometry does not resolve and the map stays at
  world scale instead of zooming to the buffer.
- `configure_worksheet_style(panes_style={"2": {"mark_style":
  {"mark-transparency": "0", "has-stroke": "false"}}})` makes the zoom ring
  invisible.
- `add_dashboard_action(action_type="parameter", aggregation="min"/"sum")` sets
  the latitude and longitude from the Apply sheet's `Location Lat`/`Location
  Long` details; `field_mappings={"True": "False"}` removes the button highlight.
