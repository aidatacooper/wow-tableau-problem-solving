# WW20 state contributions with add/remove set actions

Article 2020-05-15; official Week 20 challenge 2020-05-12, WordPress 3670. The locked source Hyper contains State, Sales, Order ID and Customer ID. Only extracted data and public SDK APIs enter the builder.

The initial selected set is Alabama, Illinois, Kentucky and Virginia. A filled generated-geography map adds selected state marks to the set; the selected list removes marks. Both select actions keep set members on clearing. A True-to-False filter action clears map selection. Sales and order bars compare In/Out contributions to the visible data total; the customer bar uses distinct customers in selected states divided by all distinct customers, with its complementary gray background. Summing customers per state would double-count people and is explicitly prohibited by the independent oracle.

REST states default, selected-only State filter, and Alabama-only State filter cover all five worksheets and expose every state metric and list member. These states do not mutate set membership. Additional add-California/remove-Illinois/clear-retains/empty outcomes are independently computed and paired with native action contracts, not browser execution. FIXED customer share remains global under ordinary State filters, while visible sales/order percent-total bars recompute. Final full worksheet CSV and paired images pass, with the reviewed hash and documented acceptable_delta in evidence/visual-review.md. No pixel equality is claimed.

## Percentage export precision

The final contribution measures use native `p0.0%` formatting (one decimal, ?0.0005 ratio rounding). `p1%` is not a decimal-place directive: Tableau interprets its numeral as literal label content. Full In/Out CSV ratios are compared independently; correct-looking bar lengths alone do not establish correct displayed percentages. Explicit Field addressing resolves the qualified native In/Out set instance and spans the two coloured bars. A formula WINDOW_SUM with Rows would partition separately by colour and produce100% in both groups; it is not equivalent to the source quick PctTotal Rows metadata. Customer share retains global distinct customer numerator/denominator.

## Final layout verification

The empty-workbook builder mirrors the source dashboard regions: three metrics at the top, an 807-pixel-wide map on the left, and a compact gray removal sidebar on the right. All metric views use the original fit-width contract; the map uses entire-view, and State List uses fit-width. The customer percent axis is primary, the full-width gray bar is the folded secondary axis, and reversed fold rendering keeps the selected purple contribution in front. Both customer axis heights are 32. Native descending membership ordering puts Sales/Orders selected segments on the left. Percent measures retain one-decimal CSV precision, while axis labels use whole percentages.

Released SDK 56377c5b170f0df1f5cd853fc483de26962dfed1 passes the independent input, calculation, action and layout contracts and all 30 worksheet CSV comparisons across three REST states. All six paired images were inspected. The final accepted artifact is 0d4e7ef4677364fad92333f9449498d7ed26c39cf6da207913c79b8416964482. Remaining bar thickness, map tone/extent and typography/spacing differences are explicit in the final visual review. No browser events were executed.
