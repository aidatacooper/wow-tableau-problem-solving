# Cloud REST review

Result: acceptable_delta. The reviewed replica is SHA-256
`af050d4220864f079f25e821f1491d16a242def927494dda9830ef2a9ae25321`.
The author comparison is an analysis-only archive exposing its Table v2
worksheet for REST CSV export. Original and comparison hashes are recorded
in export-provenance.json.

All three captured parameter states show the selected heading and downward
arrow. Sales sorts Phones ($330,007) before Chairs ($328,449); Sales / Order
sorts Copiers ($2,199) before Machines ($1,690); Profit Ratio sorts Labels
(44%) before Paper (43%), ending with Tables (-9%). Each state retains all
17 subcategories and three independently encoded metric columns. Bookcases,
Supplies, and Tables use red marks for negative profit; other bars are gray.
The latest Profit Ratio image was retried after an initially blank REST
render, and now contains the complete visible header.

The header uses 100 pixels rather than the official 50 pixels and the
reference workbook's 68-pixel object. Shorter generated headers were clipped
by the Cloud renderer. This explicit layout allowance creates more space
above the table and shifts its start to y=151; the table ends at y=680.
The left header spacer is white rather than gray. Typography, attribution,
reference-link size, stripe thickness, and pane spacing differ from the
reference. Sales / Order labels are left-aligned rather than the requested
right alignment, and the Profit Ratio zero line is solid rather than dashed.
These differences are visible and documented; this is not pixel equality.

Independent fact-level Hyper aggregation verifies Sales as SUM(Sales),
Sales / Order as SUM(Sales)/COUNTD(Order ID), and Profit Ratio as
SUM(Profit)/SUM(Sales). All six Table CSV exports cover 17 subcategories x
three pane marks (306 exported marks total), including every metric and all
three sort-key states. Header/button CSV is not used as table-data proof.
CSV row ordering is not used to certify visual ordering; the corresponding
images establish the displayed descending order.

Artifact checks verify the select event, Header v2 source, virtual Measure
Names source field, Sort (copy) target, keep-current parameter clearing, and
True-to-False self-filter with show-all clearing. REST parameter states do
not execute these actions. No browser click, hover, or tooltip execution is
claimed.
