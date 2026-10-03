# Analysis

Article date: 2020-02-09; official challenge 2020 WW06 was published 2020-02-04
(WordPress post 3458). The scope is one worksheet in a 600 x 800 dashboard,
with Sales, distinct Orders, Units, and overall health by 17 subcategories.
The builder reads only extracted Hyper and begins with TWBEditor("").

A date parameter drives Current Month and Previous Month. The default compares
November 2019 to October 2019; December 2019 and January 2019 are additional
REST states. Neither month is hardcoded into the metric formulas. Each health
ratio is current/prior, with green at >=100% and gray below. Orders use COUNTD
Order ID, units use SUM Quantity. Overall score is the count of healthy
indicators divided by three; a red dot appears when fewer than three pass.
The input oracle computes each total from facts for every state/subcategory.

The four independent panes avoid Measure Names/Values. Three bar panes use
fixed [0,1] axes; the text pane uses MIN(0.5). Public custom-tooltip APIs bind
the current/prior date, values and ratio per metric, and a separate summary
message. Tooltip acceptance verifies serialized text/field runs, not executed
hover. Official green #01665e is used; the author's slight #01625a difference
is a documented source variance. Labels and table cells use Tableau Regular.

Baseline SDK 0.27.1 / 12aae31 builds the contract without enhancement.
Cloud REST images and complete worksheet CSV review passed for all three date states; the final accepted scope and remaining visual differences are recorded in `evidence/visual-review.md`.

## Layout polish

Layout polish aligns each metric header with its own pane, increases health mark thickness, removes banding and uses white three-pixel column dividers, emphasizes row/overall labels and places the month control above restored attribution/link footer. Health cell axes use1.03 only for a narrow inter-column visual gutter; the overall axis remains0..1. Business calculations and17-row scope are unchanged.

The previously accepted workbook and complete evidence snapshot are retained in ignored scratch/polish-baseline-ww06. The polished artifact has been recaptured and accepted with documented visual differences; `evidence/visual-review.md` binds the final workbook hash and full evidence scope.
