# WW19 Cloud acceptance — Regional Sales Readout

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
Captured hashes are recorded in `evidence/cloud-verification.json`. SDK `4cd2c61`
(0.27.1).

The challenge (Ann Jackson) asks for a single-sheet map segmented by region, each
region's border in its own colour, cities sized by sales, and a hover readout of
the hovered city's sales and share of its region — with no table calculations or
LoDs.

## What was checked

- **Data**: the locked extract has 9,994 rows across four regions and 49 states;
  the verifier recomputes the per-region sales totals independently
  (`evidence/functional-verification.json`, `outputs/cloud-*-map.csv`).
- **Segmented map**: the map draws US states (geocoded with a United States
  context) and the base layer colours them by Region.
- **Region borders**: four region layers each carry their own stroke colour
  (`#7ec886`, `#82d7d6`, `#b6b6dd`, `#fd8b59`), matching the article.
- **City layer**: a Circle layer details by City and is sized by `SUM(Sales)`.
- **Region sales text**: a Text layer labels each region with its sales.
- **Interaction contract**: a `Selected City` set plus an `edit-group-action`
  (hover) stores the hovered city; `Selected City Sales`, `% of Total Sales`,
  `Selected City Name` and `Selected City Sub Text` read it back.

## Accepted visual differences

- The article's custom "Region, created from State" geographic role is not
  exposed by the SDK. The replica instead builds one State-geocoded field per
  region, which produces the same region geometry and coloured borders. This is
  recorded as a `capability_gap`.
- The selected-city readout is a separate text sheet layered over the map rather
  than living on the Sales Text marks card, because the SDK's custom-label
  resolver cannot traverse the set calculation. The interaction and values are
  the same.
- Fonts, exact stroke widths and the map washout differ slightly.

## Not claimed

This is not a pixel match, and no browser hover or set-action execution is
claimed. The author's published thumbnail is a Tableau placeholder, so the
comparison uses the article's written specification and the native contracts.
