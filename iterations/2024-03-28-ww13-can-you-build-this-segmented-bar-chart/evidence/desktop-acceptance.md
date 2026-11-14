# Desktop and hover acceptance — completed 2026-11-14

Open outputs/replicated-workbook.twbx using the selected SDK artifact and record its SHA256, Tableau version, LOADED log evidence and screenshot. Do not rebuild after binding evidence without recapturing it.

1. desktop-load: Tableau must load without errors or unknown verdict.
2. rendered-pairs: one sheet, 17 ordered sub-category rows, largest (Chairs) first; each has one taller total bar above four annual segments, all tan with white separators. Total and segmented bars have the same full length. Labels align with total bars. There is space between category pairs. Dashboard is 1000x800 and contains all 17 rows without clipping.
3. tooltip-hover: hover the total bar for Chairs and verify Total Sales against numerical-acceptance.csv; hover each of Chairs' four annual segments and verify year, annual sales rounded to whole dollars, and share formatted to one decimal percent. Repeat total and four segments for the last category (Fasteners). In particular, 2022–2024 tooltips must show the annual amount, not the cumulative segment endpoint. Record observed values, preferably hash-bound screenshot evidence.
4. visual-format: compare to the source article reference: cream background, tan bars, white separators, brown bold right-aligned labels, no visible axes/gridlines. Record acceptable differences explicitly. Parent may assign acceptable_delta only with actual author and replica visual evidence.

Status: PASS. The parent's frozen `desktop-live-acceptance-20261114.json`
records actual Tableau Desktop presentation-mode observations for all ten required
hovers, with hash-bound `desktop-hover-*.png` screenshots. Total and annual dollar
amounts and annual shares reconcile with `outputs/numerical-acceptance.csv` at the
displayed precision. The accepted primary workbook SHA256 remains
`5a6f759ecd2c8e8c09b4b9adae754e1c921eec069f406fb1ac221426c7a55b22`.

The actual author `article-reference.gif` and its `article-reference-frame0.png`
were compared with `desktop-presentation-20261114.png`. All 17 ordered pairs,
full labels, cream background, tan bars, white separators and hidden axes/gridlines
are accepted without clipping. Title/footer wording and font sizes differ:
`visual_status: acceptable_delta`. Functional acceptance is complete.

Earlier load and full 50-case corpus evidence remain unchanged. This finalization
consumes the parent's frozen observations; it performs no new Desktop or SDK run
and does not rebuild the primary workbook.
