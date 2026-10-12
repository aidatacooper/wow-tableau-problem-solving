# WW17 Cloud acceptance — Generation Populations

Accepted as `replicated / acceptable_delta` for the desktop functional scope.
Replica SHA-256 and captured hashes are recorded in
`evidence/cloud-verification.json`. SDK `4cd2c61` (0.27.1).

The author image (`outputs/cloud-author.png`) shows the target: 101 bars for
birth years 1919-2019 grouped into seven generation panes, each pane headed by
its rank, name and "total | percent", the generation's first year drawn as a
vertical label, and dashed dividers between panes on a warm background. The
replica (`outputs/cloud-replica.png`) reproduces the structure, the seven
generations, the totals, the ranks and the year labels.

## What was checked

- **Data**: the Cloud CSV export of the replica Chart worksheet returns all 101
  birth years for `SEX = 'Total'`, and every per-year population matches the
  locked-extract oracle exactly. The seven generation totals and their dense
  ranks also match (`evidence/functional-verification.json`). The dual-axis view
  emits one CSV row per pane, so rows are de-duplicated by birth year.
- **Structure**: the Chart sheet has a Bar pane coloured by the alternating
  shading field and a tiny transparent Circle pane labelled with the generation's
  first year; dashed `table-div` dividers and the `#dcd2c4` background are
  present; the `SEX = 'Total'` filter is applied.
- **Sorting**: `Min Year per Generation` is the outer column, so panes run
  chronologically rather than by rank.

## Accepted visual differences

- The replica's year member headers are hidden and the first-year labels render
  via the rotated Circle pane; the exact rotation and label placement differ
  slightly from the author.
- Fonts (the author uses Courier New headers), the exact teal shades and the
  background tone are close but not pixel-identical.
- The replica shows a stray "Population [Millions]" axis title and slight
  spacing differences; these do not change the answer.

## Not claimed

This is not a pixel match, and no browser hover or tooltip execution is claimed.
Acceptance covers the Cloud REST export and the native workbook contracts.
