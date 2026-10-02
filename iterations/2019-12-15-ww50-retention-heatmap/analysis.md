# Cohort retention with a marginal histogram

The question is how many first-time customers return after a configurable 10?26 week interval. Customers belong to the Monday of their earliest observed order. The heat map contains weeks 1 through N?1; only cohorts with customers observed at week N are shown. The marginal bars show week N, with the same cohort rows. The headline is the combined returning-customer percentage.

The input contains 359,574 customer-week records, one record per customer/week. `cohort_oracle.py` queries Hyper directly and calculates every legal period, all matrix cells, all marginal bars and the headline. It retains two denominator hypotheses: cohort size counted once, and cohort size repeated per filtered physical record. Tableau FIXED aggregation can deduplicate internally, so formula inspection alone does not establish which semantics are observed; Cloud CSV and visible percentages decide this.

The builder starts with `TWBEditor("")`, reads only the preserved Hyper, and uses public SDK APIs for FIXED calculations, conditional filters, square marks, layered bars, parameter slider, tooltips and floating layout. No original workbook XML is imported. Original TWBX is analysis/publishing evidence only.

Cloud acceptance covers REST PNG exports and the actual worksheet scope of CSV exports for periods 26, 10 and 18. A dashboard CSV that returns only the BAN is explicitly insufficient to prove the heat map. Full matrix correctness combines independent Hyper oracle, artifact formulas/filter contracts and visible image cells; extra worksheet exports are used if Cloud exposes them. No browser interaction is claimed.
