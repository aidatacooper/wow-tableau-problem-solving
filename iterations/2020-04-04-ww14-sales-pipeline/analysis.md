# WW14: sales pipeline

Each of 1,000 input records has a current stage and value. Stages are Prospect, Lead, Qualified, Opportunity, Negotiations, Closed. The current-status column sums values by current stage. Overall funnel sums the current stage and all later stages; the running/window table calculations therefore compute a reverse cumulative amount. Percent to Close is the global Closed value divided by each cumulative funnel amount, reaching 100% at Closed. Independent totals: full pipeline $1,807,416; Closed $84,153. All six stages and all current, cumulative and ratio values must be checked, not inferred from one CSV row.

Replica retains the author's FIXED closed-value and RUNNING_SUM/WINDOW_SUM calculations and explicitly addresses table calculations down all stage rows. Dashboard lays out three independent worksheets instead of the author's one sheet with three axis pairs. Percent has a synchronized dual axis with light-green MIN(1) full bars behind dark-green closed ratios. This is a public API composition choice; stage order, all values and 100% background behavior remain required. A separate Data validation table matches author Data scope and exposes current, running, window, cumulative, closed and percentage metrics.

No actions or interactive states exist in the author. Acceptance uses the default paired REST image, the full six-stage Data export and hash-bound calculation/pane contracts. No browser interactions are claimed. Tableau's FIXED LOD reaggregation is checked against independent closed-total ratios in Cloud; no arithmetic correctness is inferred solely from serialized formula equivalence.


## Layout polish

Public SDK styling preserves calculations and data. The polished artifact aligns the three metric columns at a common top and height, uses eight-point headings and stage labels, and adds visible native horizontal separators between the six stage rows. The final paired REST render and complete six-stage CSVs have been checked and accepted with documented visual differences. `evidence/visual-review.md` records the final workbook hash, acceptance scope and remaining differences.
