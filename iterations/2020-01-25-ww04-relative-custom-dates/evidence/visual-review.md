# Cloud visual review: 2020 WW04

Reviewed all four paired author/replica REST images against the frozen replica
`dd967cd1f4dae9f32531404f5a9f6634acdf9c2d7b12a29db5998abac2ed2cca`.
The result is `acceptable_delta` within the agreed Cloud REST/data and artifact
contract scope. The images are not pixel matched; the differences below are
visible and retained explicitly.

| State | Observed paired result |
| --- | --- |
| Default / Last 14 Days | First selector circle filled; no N/date controls; $34,668 sales, 17.1% ratio, $5,936 profit; matching 14-date daily trend. |
| Last 30 Days | Second circle filled; no N/date controls; $83,829 sales, 10.1% ratio, $8,483 profit; matching 29-date daily trend. |
| Last N Days / 60 | Third circle filled; only N Days input is displayed with 60; $202,277 sales, 9.0% ratio, $18,173 profit; matching 59-date daily trend. |
| Custom Dates / 2019 | Fourth circle filled; only Start Date and End Date controls appear, displaying 1/1/2019 and 12/31/2019; $733,215 sales, 12.7% ratio, $93,439 profit; matching 322-date daily trend. |

Evidence images are `outputs/cloud-{author,replica}.png`, and the corresponding
`-last30`, `-last-n`, and `-custom` image pairs. All four replica selector options
are visible. KPI numbers appear above captions in teal, and daily sales retain
the edged area composition with date labels. No browser click, hover, or date
input event was executed; parameter states were requested through REST.

Retained visual and implementation differences:

- The replica allocates 100 pixels to Selector to avoid Cloud clipping text marks
  in the 45-pixel zone. KPI and trend panels move downward and the trend is 52
  pixels shorter. The selector's quantitative -1/0/1 tick marks and repeated
  choice axis titles remain visible beneath its circles; the author hides these.
- Text circle symbols replace the author's shape palette. The replica selector
  background is white rather than the author's pale gray panel, and spacing and
  font weight differ.
- Native dynamic zone visibility replaces the original transparent offscreen
  sheet mechanism. N Days has a visible caption and a different location; custom
  date controls retain the same values and conditional display.
- The replica suppresses horizontal gridlines, uses different automatic tick
  spacing and plot margins, and retains different title/footer alignment, font
  weight, footer attribution, and link styling.

Data acceptance is independent of the image review. `cloud-data-checks.json`
checks all three KPI values and every daily date/value in all eight exports.
Trend CSVs contain two identical copies per date from the overlaid axes; each
copy is verified against the oracle and totals are not doubled. Selector/button
CSV is not used to establish data correctness. `cloud-verification.json` binds
the current workbook hashes and each image/CSV hash; `functional-verification.json`
records the independent Hyper oracle and serialized selector action/visibility
contracts.
