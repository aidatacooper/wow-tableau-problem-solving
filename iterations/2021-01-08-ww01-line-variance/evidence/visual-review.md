# WW01 Cloud acceptance

Accepted as `replicated / acceptable_delta` for the desktop functional/layout scope. Frozen workbook SHA-256: `0277a239831ed22cf3d41c311a906ba671294525faeaf1332bd632210944e42a`. SDK: `fe9f33b4dfbe5b1ecec7c56d41138a2888971375`.

All six author/replica image pairs were reviewed: 2018 Previous Year, 2018 First Year, 2018 Most Recent Year, 1995 Previous Year, 1995 First Year and 2011 First Year. Twelve PNGs and 24 CSVs are bound to this artifact by Cloud evidence and export provenance. The trend contains all 25 annual facts; comparison circles are black and selected circles pink. Selected years are visible, including 2018, 1995 and 2011. Headers show the corresponding 11%/12%/15% values, negative changes of 0.7 and 0.9 percentage points, positive changes of 0.5 and 3.0 points, and N/C at missing/zero-change boundaries.

Each of the twelve Viz exports contains the complete 75-row domain (25 years across the line and two sparse marker layers). Each of the twelve Data exports contains all 250 year/measure cells (25 years by ten measures), including explicit nulls. Both authors' and replicas' values are checked against extracted raw data and independent calculations. Raw business coverage additionally checks all 75 year/comparison combinations; those are oracle scenarios, not 75 executed Cloud states. Numeric comparisons respect exported display precision: raw diagnostic values use exact tolerance; formatted Viz values use half the displayed decimal step. Empty marker values and boundary nulls are checked explicitly. The native verifier checks real Multiple Values binding, addressing order, nested table-calculation contexts, parameter domains/aliases and synchronized axes.

Accepted visual differences:

- The narrow native comparison card sits slightly below the subtitle baseline; the year card also has a small baseline offset. Compact values such as Pr../Fir../M.. and 20../19.. truncate in the original as well. The replica's selected-year heading remains unobscured.
- For missing and zero differences, the author title renders the literal `None`; the replica leaves the null value blank. Both display N/C and preserve the same numerical/null semantics in the full exports.
- Small title/plot margins, axis positions, font spacing and footer differences remain. The replica includes SDK attribution and renders the footer link with different color styling.

This is not a pixel match. Acceptance covers Cloud REST parameter states and native workbook contracts; no browser clicks, hover execution or author-generated phone layout are claimed. The isolated zero-workbook rebuild and independent raw/native verifier establish construction from public SDK APIs and extracted inputs without an author workbook template. Rejected intermediate captures remain diagnostic scratch evidence and are not used for acceptance.
