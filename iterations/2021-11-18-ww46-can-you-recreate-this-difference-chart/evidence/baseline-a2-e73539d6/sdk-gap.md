# Generic SDK follow-up for parent

Reproduce offline with the published installation selected in run_local.ps1:

    python iterations/2021-11-18-ww46-can-you-recreate-this-difference-chart/verify_replication.py --sdk-probe

The synthetic constant-calculation fixture contains no author workbook or data. The emitted filter and manual-sort dictionary are identical in both alternatives. With Anchor omitted there are three values in each; with Anchor included there are four in each, creating an additional bar. The chart requires the three-value filter and four-value sort together. evidence/sdk-probe.json preserves exact emitted references and SDK module/version.

Suggested reusable primitive: optional measure_names_order on layered charts, independent of measure_values. Resolve and include its field instances in worksheet dependencies, but do not add those fields to Measure Values or the filter. Emit the provided order into manual-sort. Preserve defaults for existing callers and validate missing/duplicate references. Carry the option through builder_layered.py -> dispatcher -> Python facade -> MCP schema -> capability registry. Add a synthetic XPath regression asserting filter members [Earlier,Later,Spacer] and sort [Earlier,Later,Anchor,Spacer], with no Anchor in Measure Values. Do not name any API after this case.

Separately, MIN(NULL) currently resolves NULL as a field name. Strict blank workbooks raise KeyError; the initial Hyper-connected probe auto-registered a string field. Anonymous expression support would remove the physical nullable-column workaround, but that gap does not prevent numeric correctness in this implementation.

No shared SDK changes or external issues/PRs were made. Exact rendered row spacing remains unclaimed until the first primitive is fixed and Desktop confirms behavior.
