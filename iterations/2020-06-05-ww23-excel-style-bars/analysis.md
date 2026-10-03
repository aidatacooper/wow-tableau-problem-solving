# WW23 Excel style grouped bars

Article: 2020-06-05. Official challenge: 2020-06-02, WordPress post 3741.

The business question compares monthly sales across 2016?2019. The locked Hyper contains exactly 9,994 sales transactions; all 48 year/month totals are independently recomputed. Four bars share a continuous date axis with year-specific offsets -9/-4/+1/+6 days. Native custom size is four axis days, avoiding automatic widths changing with canvas dimensions.

The source jitters actual original-year dates before normalising to 2019. Its March 2016 mark falls on February 21, 2019 due to leap-year arithmetic. Normalising first would give February 20; we deliberately preserve author semantics, including this one-day placement, rather than silently substituting the article alternative.

Source workbooks are analysis only. The builder starts empty and reads only the locked Hyper. Author comparison exposes hidden Bars/Legend worksheet windows for CSV; worksheet formulas, layouts and packaged data remain unchanged as documented in export-provenance.json.

Acceptance: ww23-monthly-sales, ww23-bar-placement, ww23-cloud-bars. Static contracts cover axis-unit size, mark type and palette. Cloud CSV must cover all 48 sales marks; legend CSV cannot establish sales correctness. Rest parameter/filter states and artifact contracts are the interaction boundary; no browser actions are claimed.

Baseline SDK validation rejected native left/right mark alignment. The generic enum extension now permits the exact author left alignment; Cloud review remains pending.
