# Runtime acceptance: completed evidence and remaining events

Current artifact: `outputs/replicated-workbook.twbx`, SHA256
`7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb`.

Completed, with separate committed evidence:

- Parent Desktop native-log verdict LOADED for this exact artifact
  (`desktop-parent-check.json`); regression corpus 50 LOADED, no FAIL/UNKNOWN
  (`desktop-corpus.json`).
- Cloud REST PNG and CSV states N=1,5,16,17 (`cloud-verification.json`,
  `cloud-csv.json`). Contribution summaries 14/56/100/100% are readable;
  17 detail ranks and group subtotal values are correct; subtotal rank prefixes
  are blank, including singleton groups N=1/16. N16 retains nonzero Fasteners.
- Independent rendered/data/static review found no confirmed defect within
  that scope (`independent-final-review.md` and hash-binding JSON).

**Remaining manual acceptance: not executed; browser MFA unavailable.**
REST parameter requests and configured XML actions do not establish these events.

1. Use the actual pTopN dashboard control to change N through 1,5,16,17. Confirm
   the summary, inner pie grouping and table membership update together with
   global ranks unchanged. Check the same totals recorded in numerical-oracle.json.
2. At N=1,5,16 hover both top and rest table detail rows, group subtotal marks,
   outer-ring segments and inner-pie segments. The matching Sales Group should
   highlight across Contribution Pie and Highlight Table in either direction.
3. Leave each source mark and verify the highlight clears. Confirm no filtering
   changes the sales amounts, total denominator, or number of category marks.
4. At N=17 hover either business view: all 17 categories belong to the sole top
   group. Confirm no nonzero rest group appears and leaving restores the view.
5. Confirm Contribution Summary is excluded as both hover source and target.
   Capture actual event evidence, date, artifact hash and observable outcomes.

Keep functional_status partial and verification_status pending until these
checks are recorded. Visual acceptable_delta covers the static reviewed states,
not interactive event execution. Rebuilding invalidates this capture binding;
all new acceptance evidence must identify the new artifact hash.
