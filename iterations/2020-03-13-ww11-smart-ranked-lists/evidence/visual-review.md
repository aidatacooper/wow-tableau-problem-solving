# Cloud REST visual and data review

Reviewed all six paired dashboard PNGs for `default`, `monday`, and `year-end`, bound by `cloud-verification.json` to replica SHA-256 `70308ff09fae0b0b4449b649c274fedb5f55c5e6648eac28718463e88befdebe`.

All three ranked tables are readable in each state: sales currency is fully visible, above/below-average headings appear vertically, and maximum, above-average, below-average, and minimum cells use the corresponding green, olive, yellow, and orange colors. The selected-date arrow appears in the default and Monday states. The year-end date has no underlying orders in either workbook, so both show `#None` and no selected-date arrow. The Monday state visibly shows ranks 4, 1, and 1.

The independent Hyper oracle checks all dates and measures in all eighteen complete worksheet CSVs: 12 dates in the default state, 13 on Monday, and 12 at year-end. It verifies sales, distinct orders, quantity, average groups, color buckets, selection arrows, inclusive 84-day weekday windows, and valid selected-date rank ranges. All comparisons pass; the exported tables cover the entire data represented in these screenshots.

Accepted differences include lighter date fonts, a plain visible date control rather than the author's calendar icon, white date/header backgrounds rather than the author's broad gray below-average bands, title spacing, and simplified footer attribution. Equal-valued dates appear in a different order: notably default orders displays selected-date rank 3 in the replica and rank 5 in the author, within the same three-way tie of five orders occupying ranks 3–5. Other tied rows also reverse order. The verifier accepts the valid tie range for native `RANK_UNIQUE`; it does not claim identical tie ordering or rank identity where values tie.

Result: `acceptable_delta`, not a pixel-identical reproduction. Acceptance covers Cloud REST data/image states and workbook parameter/table-calculation contracts. No browser clicks, hovers, or other action events were executed.
