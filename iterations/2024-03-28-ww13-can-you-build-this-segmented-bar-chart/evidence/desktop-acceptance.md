# Desktop and hover acceptance — pending parent execution

Open outputs/replicated-workbook.twbx using the selected SDK artifact and record its SHA256, Tableau version, LOADED log evidence and screenshot. Do not rebuild after binding evidence without recapturing it.

1. desktop-load: Tableau must load without errors or unknown verdict.
2. rendered-pairs: one sheet, 17 ordered sub-category rows, largest (Chairs) first; each has one taller total bar above four annual segments, all tan with white separators. Total and segmented bars have the same full length. Labels align with total bars. There is space between category pairs. Dashboard is 1000x800 and contains all 17 rows without clipping.
3. tooltip-hover: hover the total bar for Chairs and verify Total Sales against numerical-acceptance.csv; hover each of Chairs' four annual segments and verify year, annual sales rounded to whole dollars, and share formatted to one decimal percent. Repeat total and four segments for the last category (Fasteners). In particular, 2022–2024 tooltips must show the annual amount, not the cumulative segment endpoint. Record observed values, preferably hash-bound screenshot evidence.
4. visual-format: compare to the source article reference: cream background, tan bars, white separators, brown bold right-aligned labels, no visible axes/gridlines. Record acceptable differences explicitly. Parent may assign acceptable_delta only with actual author and replica visual evidence.

Status: PENDING. No Desktop process started by this worker; no runtime/visual acceptance asserted.
