# Cloud review ? 2021 WW04

Final artifact: `9e27bf95043518018f7d85db9c2fff3d6854cc94074f34b912f1381bc1fafef7`. Built with immutable noneditable Git SDK `85643b0866f6d3b3cdf07c3f61762cd586a67589`.

The source and replica default dashboard PNGs were viewed side by side. The 1366?768 layout preserves the question title, signed-profit subtitle, state choropleth and city-circle overlay, complete profit legend, loss-first city bar list and challenge footer. All size legend labels, including $40,000 and >$62,037, are visible. Native legend circles are cropped vertically in the same manner as the original Tableau legend.

The accepted visual result is **acceptable_delta**: title and legend font weight, top padding, map vertical position and legend position differ slightly; the replica bar pane has a white rather than gray background. Footer typography and SDK attribution differ. This is not pixel equivalence. The default PNG shows the first scroll viewport of the bar chart; it does not display all 604 cities simultaneously.

All four REST CSV files are independently checked against 9,994 raw Hyper facts. Both Map exports contain 653 complete keys (49 state and 604 city/state); both Bar exports contain every 604 city/state key. Profit totals, positive/negative tooltip values and sign classification match the raw oracle. Currency values exported at zero decimals use a 0.501 rounding tolerance. Total raw profit is $286,397.0217. PNG and CSV hashes bind the final artifact and the separately published analysis-only source export.

State-pane inert interaction and Bar?Map hover highlight source, target, City/State Abbrev fields and automatic clear are verified from the generated native artifact. No browser hover, tooltip display, scrolling or clicking was executed. The builder starts from TWBEditor empty, reading locked Hyper/CSV inputs and public APIs; no source workbook is a construction input. Earlier rejected alphabetical-order/legend captures remain scratch diagnostics and are not final evidence.
