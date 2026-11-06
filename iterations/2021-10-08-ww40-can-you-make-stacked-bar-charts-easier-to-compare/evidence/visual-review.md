# WW40 final visual review

The original author and revised replica dashboard screenshots were reviewed in all three parameter states. The original workbook was not altered; it exposes only the dashboard on Cloud. The selected category sits at the bottom of both A-M/N-Z stacks, matching the author:

| State | Stack top to bottom |
|---|---|
| Office Supplies (default) | Furniture, Technology, Office Supplies |
| Furniture | Office Supplies, Technology, Furniture |
| Technology | Office Supplies, Furniture, Technology |

Both bars preserve their total height between states; the printed totals remain $1,128K and $1,169K. Category labels agree in all states: A-M Furniture $353K, Office Supplies $381K, Technology $394K; N-Z Furniture $389K, Office Supplies $338K, Technology $442K. Colour mapping and white labels agree. The corrected worksheet title now includes Sales by Category, the selection instruction and all three colour-key category names. Both screenshots use the same 400x800 dashboard size (800x1600 exported pixels).

Accepted visual differences: the grey title banner is centered rather than left aligned; outer margins, plot baseline and bar heights differ slightly; very light pane borders remain; footer typography and the replica credit differ. These do not change the grouping, totals, categories, baseline comparison or interaction instructions. Result: acceptable_delta.

The first capture omitted the worksheet title and was rejected as a usability defect. This final review applies only to the recaptured bf9a32d976c9f7aca2793ecf6ab981db1c5f22ca2b9d126ee73d54d9003767c5 artifact. Its data verifier passes 90 checks over all three states, with exact Sort/boolean comparison and $500 tolerance for currency displayed as whole $K. Desktop LOADED, Cloud image capture and CSV exports are bound to the same artifact. Verification scope is REST parameter states plus native action serialization; no browser-click claim.
