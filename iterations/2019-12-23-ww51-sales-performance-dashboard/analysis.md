# Sales performance dashboard

This dashboard combines six views over Superstore: weekly sales area, year selector circles, monthly sales bars, monthly subcategory dot matrix, subcategory sales marginal histogram, and a state filled map. The shared custom brown gradient indicates sales. Dot-matrix and marginal-histogram rows sort by total subcategory sales, so their identities align.

The original defines one year-selection filter action targeting the whole dashboard and one on-hover highlight action shared by the bottom three charts (monthly bars, dot matrix and subcategory bars). Map, weekly chart and year selector are excluded from highlight source and target. The original has no map-selection filter action; this reconstruction does not invent one.

The builder starts empty and reads only preserved input Hyper. Original XML was inspected during analysis to record chart grains and fixed layout constants; it is neither opened nor copied during construction. `sales_oracle.py` queries Hyper independently and sums weekly, monthly, subcategory, subcategory-month, state and year grains. Totals reconcile for default, 2019, California, and 2019+California.

REST image and CSV filters are data-state checks, not evidence of browser action execution. Dashboard CSV scope is recorded based on actual columns and rows, and is insufficient by itself to prove all six chart datasets. Actions are accepted through explicit source, targets, event and clear behavior artifact contracts.

Cloud diagnosis exposed two SDK expression/encoding problems: explicit date expressions needed recognition by the public field registry, and repeating an ordinal month/year shelf field as a tooltip encoding could blank an otherwise valid worksheet. Generic SDK fixes and synthetic regression tests address these failures; the case uses public date expressions and custom tooltips.

Weekly dates explicitly use Sunday. Independent raw-Hyper Sunday and Monday aggregations were fitted to the author's actual Cloud area silhouette at all four states; Sunday error was consistently much smaller, including 1.11 versus 226.24 square pixels for 2019 California. The final Sunday replica passes every weekly CSV value and visually matches those peaks. The comparison and fitting method are recorded in evidence/weekly-boundary-image-diagnosis.json.

All four states are accepted as replicated / acceptable_delta after actual image review and strict CSV comparison. Author CSVs expose only the marginal subcategory bars. Separate replica sheet CSVs validate every weekly bucket, month and populated subcategory/month matrix cell independently against Hyper; state map and year selector use independent Hyper totals, screenshots and workbook contracts. See evidence/visual-review.md for the exact scope and retained visual differences.
