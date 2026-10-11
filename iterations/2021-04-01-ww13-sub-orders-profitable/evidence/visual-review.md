# Visual review — WW13 profitable sub-orders mekko

## Scope

Two Cloud REST captures were taken at the default state (all three Segments):

- `outputs/cloud-author.png` — the author's published dashboard view
  (`2021_03_31_WW13_Percentage_Sub_Orders_Profitable`).
- `outputs/cloud-replica.png` — the replica worksheet (`Viz`) in the same state.

## Result: acceptable_delta

The business answer is identical. The replica reproduces:

- variable-width columns ordered Copiers, Paper, Art, Envelopes, Labels,
  Fasteners, Accessories, Appliances, Phones, Furnishings, Supplies, Storage,
  Machines, Binders, Chairs, Bookcases, Tables;
- pink upper bars whose height is the profitable-order percentage
  (Copiers/Paper/Art/Envelopes/Labels 100%, Phones 85%, Chairs 58%, Tables 36%)
  and warm-grey lower bars carrying the complement, separated by the black zero
  line;
- bar widths proportional to each Sub-Category's share of sales, with the
  cumulative axis ending at 100%;
- the pink/grey Measure Names palette.

The Cloud CSV exports agree exactly. The replica's
`% of Total Sales`, `% Total Sales Cumulative`, `Profitable Orders` and
`Non Profitable Orders` columns match the author's export row for row — for
example Phones 14% / 39% / 85% / 15%, Machines 8% / 63% / 63% / 37%, Tables
9% / 100% / 36% / 64%.

## Allowed differences

- The author's export formats Sales as currency (`"$149,528"`); the replica
  exports the raw value (`149528.03`). This is number formatting.
- The replica's bar labels are culled more aggressively than the author's, so
  only the widest columns show their Sub-Category and percentage. The reference
  screenshot also shows culled labels; the difference is which columns survive
  culling, which depends on rendered width.
- The replica sheet title reads `Viz`; the author's dashboard has no title.
- Exact fonts, padding and the footer text zone differ.
- The author's extra `Data` debugging sheet is not reproduced.
