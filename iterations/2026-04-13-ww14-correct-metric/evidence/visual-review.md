# Cloud REST visual and numerical review

Result: **replicated / acceptable_delta**. The final
[author image](../outputs/cloud-author.png) and
[replica image](../outputs/cloud-replica.png) were inspected side by side.
Identity and exported-file hashes are recorded in
`cloud-verification.json`. No browser click or hover is claimed.

## What the two dashboards show

Both render the same 649 orders from Oct–Dec 2025 as two scatter plots of
`Avg. Quantity` against discount, with orders that disagree between the simple
and weighted metric highlighted in red.

The author's dashboard carries a large explanatory text column on the right
("Quantity and Discount by Order", "Incorrect Metrics" / "Correct Metrics",
a difference slider) that the replica does not reproduce. The replica keeps the
two charts and the title, and labels each chart
`Simple average (AVG of Discount)` / `Weighted average (SUM(Discount*Quantity)/SUM(Quantity))`.
This is a presentation difference only; the plotted data and the red/grey
classification are the same.

## Numerical agreement

Both metrics were compared row by row against the author's own Cloud CSV
exports, over the same 649 orders:

| Comparison | Result |
| --- | --- |
| Order set identical | 649 / 649, no extras either side |
| `Is difference?` flag | 0 mismatches (149 orders flagged in both) |
| `Avg. Quantity` | 0 mismatches |
| `Avg. Discount` | 0 mismatches beyond the author's 0.1% display precision |
| `Weighted Avg` | 0 mismatches beyond the author's 0.1% display precision |

`Avg. Discount` and `Weighted Avg` are formatted as raw fractions in the
replica (`0.025`) where the author formats them as percentages (`2.5%`). The
underlying values agree; only the number format differs, and it does not change
the answer.

The replica's `Weighted Avg` was additionally checked against an **independent
Hyper aggregate** (`SUM(Discount*Quantity)/SUM(Quantity)` computed directly
from the packaged extract), not just against the author's rendering: 0
mismatches, worst absolute delta `5.0e-04` (exactly the author's display
rounding).

## Accepted visual differences

- The author's right-hand explanatory text column and difference slider are not
  reproduced; the replica is the two-chart dashboard only.
- Mark colouring uses the same red/grey classification but different exact
  hex values.
- Axis tick label formatting differs (percent vs fraction), as above.
- No clipped or `####` values; all marks are visible in both charts.

This is not a pixel-identical result.

## Scope and limits

`acceptance_scope: cloud_rest_and_artifact_contracts`,
`browser_interaction_executed: false`. The captures establish REST-rendered
states and exported worksheet scope. The dashboard highlight action is present
in the workbook XML and asserted by the verifier, but no browser click was
executed, so hover/select behaviour is not claimed from these images.
