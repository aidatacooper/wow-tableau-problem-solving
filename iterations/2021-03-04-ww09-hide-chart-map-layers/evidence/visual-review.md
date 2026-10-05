# Cloud visual review

Result: **acceptable_delta**. Reviewed the eight actual Cloud REST dashboard PNGs
for default, China, Russia and reset side by side. Replica workbook SHA256:
`fb41334e7d427244e7cfc0a64f61979fd6355adb1c5021f27f282e71ff337529`.
Image hashes and request parameters are bound in `cloud-verification.json`.

| State | Observed author and replica behavior |
| --- | --- |
| default | World country polygons in six region colors; no donut. |
| china | Only China geography, gray two-part donut, centered 52% urban label. |
| russia | Only Russia geography, gray two-part donut, centered 74% urban label with automatic black contrast. |
| reset | Empty parameter restores the world and removes the donut, matching default. |

The final public API build corrects the first candidate's misplaced center label,
unwanted background country names, table border and centered title. Ring size,
region colors, conditional geometry and selected-country focus match the source.
Both use one worksheet and a 1000 by 800 dashboard with four authored native layers.

Accepted differences are small title/subtitle padding, vertical map placement,
footer font weight, the white HTTPS challenge link versus the author's teal link,
and an explicit CWTWB recreation credit. These do not alter the functional result.
The result is not a pixel-identical reproduction.

REST parameter requests demonstrate state rendering. Native action source, target,
selection event and empty-value clearing are independently verified in the
artifact; no browser click, hover or deselection was executed or claimed.
