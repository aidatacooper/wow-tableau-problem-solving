# Final Cloud review: Premier League table

Result: **acceptable_delta**. Accepted replica TWBX SHA-256:
`939c2210723255e049c9727caeca18af831c108d15a7f0ed4fd336e765f393d9`.
The final builder ran through `.venv/Scripts/python.exe` after actual Git SDK
`682f45db98a23042495275d976dddaffdabbf310` was installed, as recorded in
`build-provenance.json`. No accepted artifact was rebuilt after capture.

All eight paired dashboard PNGs and 24 complete main-worksheet CSVs were
independently inspected and verified. `cloud-verification.json` binds each
export to both published workbooks and the accepted artifact. All three
packaged Hyper extracts match their locked input hashes. The raw oracle covers
every 156 pivoted team-match record and all 78 original fixtures, with mirrored
home/away goals and results checked independently of Tableau blends.

| REST state | Table metric values per role | Bar rows per role | Chronological result rows per role |
| --- | ---: | ---: | ---: |
| Default | 80 (20 teams x four metrics) | 74 | 100 |
| Arsenal | 4 | 3 | 5 |
| Liverpool | 4 | 4 | 5 |
| Chelsea | 4 | 4 | 5 |

Across both roles this is 184 table values, 170 bar rows and 230 result rows.
Each bar row is either a present W/T/L segment, including a zero-point loss,
or the total-label mark. No absent result category is invented. Every team,
metric, segment and chronological date is required exactly once. The verifier
checks every result's W/T/L classification, plot index 1..5, match points,
opposition, team-relative goals and opposition goals against the original
fixture inputs. CSV record ordering is not treated as mark ordering.

The default image shows all 20 teams sorted by descending points, with tied
teams aligned consistently across all three worksheets. Leicester leads with
18 points; Liverpool and Tottenham have 17. The four standings metrics,
stacked green wins/grey draws/pale-red zero-point losses, black total labels
and all 100 chronological last-five circles are readable. Result letters are
now centred inside their circles, with colour-matched bold labels. The
transparent, source-sized Gantt endpoint no longer produces a tall grey tick.

Arsenal's filter gives 8 matches, 4 wins, 0 ties, 4 losses and 12 points, with
W/L/L/W/L last-five results. Liverpool gives 8/5/2/1 and 17 points, with
L/T/W/W/T; Chelsea gives 8/4/3/1 and 15 points, with W/T/T/W/W. Every selected
image retains the four metric values, the correctly segmented total bar and
five readable result circles. Like the source, one-team views expand the row
and bar vertically within the fixed dashboard.

Remaining differences are visual: circles are smaller than the source;
heading/header and footer font weights and spacing differ; the replica places
some worksheet columns and row dividers slightly higher; the bar worksheet
retains a faint outline; the URL is plain text rather than the source's blue
underlined appearance. No metric, team label or result is clipped or missing.
The native datalabel/cell styles, tiny transparent Gantt marker and real exact
Date detail are explicitly asserted, so the earlier silently ignored style
and default Month grain cannot pass unnoticed. No pixel-identical claim is
made.

The source contains no dashboard actions. Native blend links use Team and
exact Date, aggregate string opponent proxies remain nominal, and primary
dependencies contain only the six real physical fact columns. All 100 default
opponents and score orientations are verified by CSV rather than inferred
from the circles. REST ordinary Team filters are exercised; browser hovering
and tooltip opening are not. The original failed unbound-pane and Month-grain
captures, followed by the numerically correct label-refinement capture, are
preserved in analysis scratch with explicit failure/refinement records.

Final direct verification passes the complete raw, packaged-data, native,
24-CSV and eight-image hash checks.
