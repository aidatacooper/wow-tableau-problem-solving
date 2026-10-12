# WW22 Cloud acceptance — can you structure the unstructured?

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
SDK `4cd2c61` (0.27.1).

The challenge (Candra McEniry, built by Donna Coles) parses free-text Airbnb
descriptions with regular expressions to derive the bedroom count, then shows a
price histogram and a Seattle map that filter each other.

## What was checked

- **Data**: the locked extract has 1,189 listings; the verifier re-implements the
  article's regex chain in Python and confirms every row is matched.
- **Bedroom parsing**: `Step 1 - Clean Up Bedroom` normalizes the many "bedroom"
  spellings, and `Step 2 - Group Sizes` extracts Studio or `\d+ Bedroom`.
- **Bedroom groups**: the categorical group maps the sizes to Studio (503), 1-4
  Bedrooms and "More Than 5 Bedrooms" (89).
- **Price bins**: `FLOOR([price]/[Bin Size])*[Bin Size]` reproduces the $100
  bins (572 listings in $0-100, 425 in $100-200, ...).
- **Histogram**: bars per price bin, the average reference line ($136) and the
  bedroom filter.
- **Map**: a `MAKEPOINT` spatial layer with listing detail, the Area Code
  Boundaries layer and a listing/price tooltip.
- **Interactions**: two Use-as-Filter actions plus a URL action on the map.

## Accepted visual differences

- Fonts, padding and the exact stroke widths differ.
- The map plots a `MAKEPOINT` field rather than the raw lat/lon columns, which
  the extract does not expose with geographic roles; the plotted points are the
  same.

## Workarounds recorded

- Tableau's internal `sys_numbin` helper is not in the released SDK's function
  catalog and did not bin correctly; the `FLOOR` form the article also documents
  is used.
- The extract's `lattitude`/`longitude` columns carry no geographic role, so the
  map plots a `MAKEPOINT([lattitude],[longitude])` field.

## Not claimed

This is not a pixel match, and no browser click execution is claimed. The
author's published thumbnail is a Tableau placeholder, so the comparison uses the
article's written specification and the native contracts.
