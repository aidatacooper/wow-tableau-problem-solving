# Final visual review: WW38 Net Change

Verdict: acceptable_delta. Reviewed original and replica Cloud PNGs for default, july-range and single-day, all bound in cloud-verification.json to frozen replica `7c019ad146c0535a29b3be0aa5090b8051779ab06e0830af91a16ec8710fc98c`.

## Functional content observed
- Default (Sep 06–20, 2021; 6 MONTHS history): South +$49.45 / +60.6%, West +$210.81 / +16.6%, Central -$1,703.21 / -89.0%, East +$6,775.29 / +1158.9%. Four rows appear South, West, Central, East in both dashboards.
- July (Jul 01–31; 1 YEAR history): South -$304.09 / -88.0%, West -$4,820.61 / -98.1%, Central -$429.64 / -67.1%, East +$548.13 / +82.5%. Negative red bands now appear behind the first three rows, and the pale positive band appears behind East. This corrects the first capture, where the negative band was covered by the later pane.
- Single day (Sep 07; 1 MONTH history): all four KPIs are +$0.00 / 0.0%; the corresponding day's trend segment is teal. A zero-width range has no filled area, consistent with a same-day selection.
- Daily trend shapes, endpoint states, gain/loss colour and selected timeframe respond in all three REST states. The selected-date subtitle matches each state.

## Evidence and limits
`verify_cloud_data.py` independently groups 9,994 locked Hyper rows, compares original Step 1/2/3/5 native values, then compares the replica Trend/KPI/Subtitle/Timeframe Selector exports. All 18,144 numeric checks pass; full history domains are 446, 852 and 89 Region-day marks. Original intermediate sheets remain unmodified. The final Desktop evidence is LOADED and has the same workbook SHA256. Native parameter and deselection action contracts are checked statically; browser drag/click execution has not been performed or claimed.

## Accepted visual differences
- Replica headings and instructions are centered; the instruction newline is collapsed before STEP 1 and wraps differently.
- Timeframe values have a faint duplicated header row and alphabetical order; selected values remain visually emphasized and native values/actions are unchanged.
- Region labels repeat in grey beside the trend and use title case; the author shows uppercase labels only in the KPI column.
- Extra Region headers narrow the trend pane; fonts, margins, line scale and footer placement differ.
- Range fills now have the correct sign and exact calendar endpoints. The author's dotted white vertical band boundaries are absent in the replica; single-day selection therefore uses the coloured trend segment and subtitle rather than a full-height dotted line.

No missing KPI rows, blank trends, changed endpoint amounts, or unresolved data discrepancies remain. These differences are presentation deltas and are not described as a pixel match.
