# WW12: missing periods and adaptive bars

The business chart counts distinct orders for a single selected sub-category, colours marks by profit, and buckets orders by day, Sunday-based week or month. A latest-year filter includes the chosen one to four calendar years. Initial state is Tables, Weekly, two years. A continuous exact-date axis leaves gaps between sparse date marks; it does not invent zero-sales records. Width is a continuous dimension (1/5/10), centred and scaled in native date-axis units.

The author has a floating vertical container holding period parameter, Selector and years parameter, initially hidden behind a show/hide button. A single-select set action assigns selected Sub-Category and retains the membership on clearing (`do-nothing`); the True-to-False self-filter clears the visual selection. Replica uses unicode empty/filled circles and labels in a Text mark in place of custom shape glyphs, retaining the same set-action source/target contract. Native toggle and axis-unit mark-sizing are reusable SDK gaps, reported using scratch/ww12-analysis/sdk-gap-source.xml and synthetic SDK regressions.

Acceptance: independent distinct-order and profit totals for every Tables date mark in four REST parameter states; exact-date continuous instance and native sizing; serialized set, self-deselection and container toggle contracts; paired Cloud images. REST cannot execute the set selection or toggle button. No browser events are claimed. The empty calendar periods are verified as sparse absent marks and a continuous date axis, not treated as fabricated zero rows.


## Layout polish

Public SDK styling preserves calculations and data. The polished artifact restores the hidden filter panel dashed border and four-pixel margins, and splits footer attribution into three columns. All four REST states have been recaptured and accepted with documented visual differences. Expanded-panel appearance and actual clicks remain outside the executed evidence scope; the serialized toggle contract is checked. `evidence/visual-review.md` records the final workbook hash and acceptance scope.
