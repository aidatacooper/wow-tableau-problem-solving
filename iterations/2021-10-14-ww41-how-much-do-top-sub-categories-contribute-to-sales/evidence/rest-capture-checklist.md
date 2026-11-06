# WW41 PAT REST capture and artifact-contract checklist

This case accepts PAT REST evidence for static image/data states and XML artifact contracts. It does not treat REST parameter injection as browser interaction.

## Current Cloud IDs

- Replica workbook: `c53f88e0-4c74-4887-b6bb-55427c51eedc`
- Dashboard view: `8322d6d6-3c45-4a58-b438-3d4298ed4dfa` (`Top Sub-Category Contribution`)
- Contribution Pie: `14beb491-9115-4671-9a83-dd4cd18e80fb`
- Highlight Table: `b3a754dc-615b-40a5-a10b-d3191242ce89`
- Contribution Summary (excluded from action source/target): `d4536c9e-febb-4e2c-b717-3b55b22c7372`
- Frozen artifact SHA256: `7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb`

## REST image/data-state capture

For each `pTopN` state `1`, `5`, `16`, and `17`, capture the dashboard PNG and CSV for Contribution Pie, Highlight Table, Contribution Summary, and Top Sub-Category Contribution. Record request URL/parameters, UTC timestamp, workbook/view IDs, file SHA256 and byte size. Compare totals, contribution percentages, membership, global ranks, and blank subtotal rank prefixes with `evidence/numerical-oracle.json`.

## Artifact-contract checks

Before accepting a capture, verify the referenced artifact hash is the frozen hash above; the dashboard is 1400x900; the only action is `tsc:brush` with `on-hover` and `auto-clear=true`; Sales Group is the matching field; Contribution Summary is excluded from source and target; no filter action is present; and the 17-category color keys and global rank addressing remain present in the TWB XML. A future capture may be checked by a script without rebuilding the frozen workbook.

## Explicitly pending browser events

Use the actual dashboard control at N=1, 5, 16, and 17, then hover and leave top/rest detail rows, subtotal marks, outer-ring segments, and inner-pie segments in both directions. Confirm highlighting and auto-clear, unchanged sales and denominator, and no Contribution Summary response. Record screenshots/event logs against the same artifact hash. Do not describe REST requests as these events.
