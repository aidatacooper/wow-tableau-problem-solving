# Cloud REST visual and numerical review

Result: **replicated / acceptable_delta**. The final
[author image](../outputs/cloud-author.png) and
[replica image](../outputs/cloud-replica.png) were inspected side by side.
Identity and exported-file hashes are recorded in
`cloud-verification.json`. No browser click or hover is claimed.

## What the two dashboards show

Both render the same 649 orders from Oct–Dec 2025 as two scatter plots of
`Avg. Quantity` against discount, with orders that disagree between the simple
and weighted metric highlighted in orange.

The replica follows the author's layout: the two scatter sheets stacked on the
left (titles hidden, `Avg. Discount` / `Avg. Discount per Order` on the x axes),
the explanatory text column on the right, the difference slider beneath it, and
the credits footer. Mark styling matches the author's translucent, smaller
circles whose value labels appear only when a mark is highlighted
(`mark-labels-mode: highlight`).

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

The replica's `Weighted Avg` was additionally checked against an **independent
Hyper aggregate** (`SUM(Discount*Quantity)/SUM(Quantity)` computed directly
from the packaged extract), not just against the author's rendering: 0
mismatches, worst absolute delta `5.0e-04` (exactly the author's display
rounding).

## Accepted visual differences

- The author's right-hand column is left-aligned paragraph text; the replica
  reproduces the wording and alignment but the fonts and exact leading differ.
- The difference slider is present and wired to the same metric, but its
  styling and the "0.0% to 16.7%" caption formatting differ from the author's.
- Axis tick label formatting and mark anti-aliasing differ slightly.
- No clipped or `####` values; all marks are visible in both charts.

This is not a pixel-identical result.

## Scope and limits

`acceptance_scope: cloud_rest_and_artifact_contracts`,
`browser_interaction_executed: false`. The captures establish REST-rendered
states and exported worksheet scope. The dashboard highlight action is present
in the workbook XML and asserted by the verifier, but no browser click was
executed, so hover/select behaviour is not claimed from these images.
