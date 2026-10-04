# Customer lifetime value matrix

Article: 2021-01-14. Official challenge: 2021 WW02, published 2021-01-12 (WordPress post 4322), https://www.workout-wednesday.com/2021w02tab/.

The question is the average cumulative value of customers acquired in each quarter, over elapsed quarters since their first purchase. A cohort is a customer's first-order calendar quarter, not the date of each order. The acquired-customer denominator is fixed per cohort and must remain constant across elapsed quarters.

## Source analysis and inputs

The original author archive was inspected only during analysis and for comparison publication. Its sole Hyper contains 9,994 original order lines with Order Date, Customer ID and Sales, spanning 2016-01-03 through 2019-12-30. There are 793 customers in 16 quarterly cohorts. The unmodified extracted Hyper is locked by SHA256 in inputs/source-lock.json. The builder reads this input and creates a new empty TWBEditor; it never reads the author archive or analysis XML.

The source uses five calculated fields: customer first-order quarter via a FIXED Customer ID MIN(Order Date) LOD; cohort customer count via FIXED cohort COUNTD(Customer ID); elapsed quarter DATEDIFF; RUNNING_SUM(SUM(Sales))/SUM(CUSTOMERS); and a nested LOOKUP calculation filling a missing cell only when both immediate neighboring average values are nonnull. Both calculation levels address elapsed quarter, partitioning by cohort/customer row headers. This does not promise arbitrary consecutive-gap filling.

There are 134 observed sales cells. Two single-quarter holes occur at Q3 2018/elapsed1 and Q2 2019/elapsed1. Domain completion plus the original LOOKUP rule produces 136 visible cells. The trailing 120 cells of the full 16x16 domain are null and excluded with the source table-calculation range [32.3575,3353.0410818181813]. The source itself uses this finite range rather than an unbounded special-not-null filter; retain that original contract for these locked inputs.

## Layout and public API choices

The desktop canvas is 1400x1000. Cohort/customer row headers and elapsed-quarter column headers frame a triangular Square heatmap, with white cell borders and dollar labels. A named palette alone does not install the original custom CB_PuBuGn preferences. The builder uses the public custom-interpolated colors API with all nine original purple/blue/green stops. Explicit bracketed cohort expressions bind exact discrete dates, avoiding the SDK's ordinary default date-month hierarchy.

The chart has one worksheet and shares one addressed User calculation instance across color, labels, range filter and rich tooltip; no per-worksheet numbered table-calculation context is required. Both outer LOOKUP and nested running sum address the explicit elapsed-quarter instance. Title/footer text zones and field-specific header formats use the public layout/style schemas.

The source has no parameters, dashboard actions, user filter cards or buttons. The acceptance state is therefore the full default matrix. Native tooltip formulas/text are checked from the artifact. No browser hover, click, device layout or phone acceptance is claimed.

## Independent acceptance

The verifier computes customer acquisition and cohort membership from raw orders, aggregates quarterly sales, accumulates each cohort's revenue, divides by distinct cohort customers, and checks both gap-fill cells. It verifies all 136 source and replica Viz REST CSV rows individually, including cohort identity, age, denominator and formatted currency value, with 0.501 tolerance only for the explicit zero-decimal currency export. It rejects duplicate/missing/extra cells. No auxiliary Data worksheet or dashboard-button CSV is used as matrix proof. Original unformatted raw calculations remain recorded in data-oracle.json.

Images require a fresh Cloud publication after every rebuild because workbook identities/hashes change. Rejected initial month hierarchy and default palette captures are retained only in local scratch, with a hash-bound refinement explanation in evidence/refinement-initial-domain-palette.json.
