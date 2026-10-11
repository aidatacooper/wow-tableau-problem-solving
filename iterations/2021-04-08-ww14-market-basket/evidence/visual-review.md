# Visual review — WW14 market basket

## Scope

Two states were captured with Cloud REST, each with the author's dashboard and
the replica dashboard:

- `outputs/cloud-author.png` / `outputs/cloud-replica.png` — default state
  (`Toggle = 0`, `pSelected_SubCat = Accessories`), the bar chart.
- `outputs/cloud-author-dash-tm.png` / `outputs/cloud-replica-dash-tm.png` —
  `Toggle = 1`, the treemap.

## Result: acceptable_delta

The business answer is identical in both states.

**Bar state.** The replica shows the same 16 Sub-Categories in the same order
(Paper 23, Binders 23, Furnishings 18, Phones 15, Storage 11, Appliances 9,
Labels 7, Chairs 6, Tables/Supplies/Machines/Fasteners/Art 5, Envelopes 4,
Bookcases 3, Copiers 1) with the same profitability colouring (Storage,
Appliances, Tables and Machines unprofitable; the rest profitable).

**Treemap state.** The replica tiles match the author's layout and labels
(Binders 23, Phones 15, Storage 11, Appliances 9, Paper 23, Labels 7, Chairs 6,
Fasteners/Machines/Supplies/Tables 5, Bookcases 3, Envelopes 4, Art 5,
Copiers 1), again with matching colours.

The Cloud CSV export of the replica Bar worksheet agrees with the author's
export row for row on `Count Orders` and on the profitability flag, and the
underlying sales/profit totals match to the cent (for example Paper
1,539.57 / 653.23 and Machines 6,683.92 / −1,948.97).

## Allowed differences

- The author's export rounds the displayed Profit/Sales to whole dollars and
  formats them as currency; the replica exports the raw values.
- The author's treemap has a slightly different tile aspect ratio and shows the
  Sub-Category label before the count; the replica shows the count above the
  label. Both label sets are the same.
- The toggle control is drawn as a two-stop slider in the replica; the author's
  version renders the same two-point axis.
- Header/footer text zones, the "CHALLENGE BY / RECREATED BY" strip, fonts and
  padding differ.
- The author's extra `Data` debugging sheet is not reproduced.
