# WW51 Cloud visual and data review

Result: acceptable_delta. Final replica TWBX SHA256: `2f76d2a090b5544cd9d840192296f3b50fba0faf7e201c99fd7f576592c635cf`.
Actual installed Git SDK: `e977401d862f0754ba610249e6720d61058ebdea` (noneditable).

All four original/replica pairs were opened and reviewed: default 2012, 2011, 2000 and 2001. The eight fresh PNGs show the complete unstacked divergent histograms, original female purple/male teal, readable colored peak labels, dynamic year heading, YEAR dropdown, hidden country-count axis, continuous 30-95 age axis, gray zero baseline and top/bottom framing. No plotted peak, title or control is clipped. The public-API polish removes the first capture's visible Count gutter, incorrect age-axis title, black peak labels and dashed center line. The archived initial capture is excluded from final acceptance.

| State | Complete Viz rows per workbook | Female/male peak counts | Positive/negative reference values |
| --- | ---: | --- | --- |
| default 2012 | 74 | 19 / 13 | 19 / -19 |
| 2011 | 77 | 21 / 14 | 21 / -21 |
| 2000 | 80 | 18 / 13 | 18 / -18 |
| 2001 | 76 | 14 / 15 | 14 / -14 |

All eight nonempty Viz CSVs pass the independent locked-Hyper oracle: 614 complete age/sex rows, each present exactly once, with every distinct-country count and both reference values checked. Null ages are excluded. The raw oracle separately checks all 5382 source records across 13 years. Male values can be unsigned in formatted CSV; signed plotting is proved by the exact conditional COUNTD formula, breakdown-off/native bar bindings and paired renders, rather than inferred from CSV formatting. The source auxiliary Data worksheet defaults to 2011 and is not used to prove the default 2012 result.

The original WINDOW_MAX signed-count formula is preserved. It returns the female peak, so in 2001 the symmetric reference values +/-14 are smaller than the male peak 15. Every male peak bar and all three 15 labels remain visible in both renders, but the zero baseline is slightly above the vertical midpoint. The all-year raw audit also identifies this reference-domain condition in 2002 and 2005; those two years have raw mathematical coverage, not exported-state visual coverage. This acceptance proves the original paired reference formulas and the four rendered states; it does not promise perfectly symmetric viewport bounds for every possible year.

Remaining visual differences are small plot offsets and framing/tick stroke thickness, heading/legend/footer typography, and the recreation footer credit naming CWTWB. The final plot and zero baseline are a few pixels lower than the original. These preserve reading and all business marks; this is not pixel equality.

Acceptance scope is Cloud REST images and complete Viz data states plus generated artifact contracts. The rich tooltip retains year, sex, age, years and country-count fields/text, verified in the artifact. No browser click or hover was executed; no phone or mobile rendering was tested. Source comparison/export changes only existing worksheet hidden-window flags, with unchanged business XML and packaged data bytes.

Direct verification and an isolated from-zero rebuild both pass on the exact Git SDK. The isolated build copies only scripts, metadata and locked inputs; original workbooks and Cloud evidence are absent. The normal comparison verifier still requires source-export provenance and exact artifact/image/CSV hashes whenever Cloud evidence exists.
