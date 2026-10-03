# Cloud REST review

Result: acceptable_delta. Reviewed replica SHA-256:
`5d059f8fb4cae12d170b830f1af96a16fe1ac975b7f9f6c9b125365376d29d67`.
Author comparison changes only worksheet window visibility for REST export;
its original and analysis-copy hashes are recorded in export-provenance.json.

November, December and January states display all 17 uppercase subcategories,
three health blocks and the overall percentage. Default November agrees on
Bookcases and Labels at 0%, and Binders, Machines and Tables at 67%, with
red alert dots on each incomplete row. Other default rows are 100% without
an alert. January Machines remains 100%; the changed health states follow
the independent fact-level month-pair oracle. All six full-table CSV exports
passed, independently checking thirteen numeric/indicator fields for every
subcategory: 1326
verified field instances across the author and replica states. The author
CSV combines panes into one row per subcategory; the replica exports four
pane marks per subcategory. These are full Viz exports, not button CSV.
The comparison accounts for actual percentage-display precision (the author
exports whole percentages), rather than treating rounded labels as exact ratios.

Remaining visible differences are lighter typography, thinner bars and larger
row gaps, thin gray separators instead of the author's white cell gaps, and
column-title spacing. The replica uses official green #01665e while the author
uses #01625a. The bottom area shows the month parameter in place of the author's
decorative attribution/link block. These deltas retain every legible health
cell, row identity and overall score; this is not pixel equality.

Serialized tooltip runs bind the subcategory, current/prior month, current/prior
metric values and ratio; the summary has its separate percentage-on-track text.
The verifier confirms one worksheet, four independent axes, no Measure Names /
Values, fixed block bounds, red alert-label styling, month-list parameter and
COUNTD order logic. No hover was executed and REST images do not prove tooltip
interaction. Acceptance consists of REST parameter states plus artifact contracts.
