# Independent review record: WW43 and text-chart SDK fix

This file preserves the independent review result supplied to the parent task.
It is a transcription, not a new independent approval by the integration agent.
Reviewer reported model **gpt-6.1-sol**.

Source: [Independent review task](t3-thread://v1/thread:delegated-task:command%3Amcp%3Ad403c1d3-bffd-4dfb-8063-c4d848e8d5c5%3Adelegate-task%3Aaefea062-4e05-4522-9cb9-53350847913a).

## Confirmed finding outside WW43

P2: cwtwb run-spec `_apply_worksheets()` allowlist omitted
`table_calc_overrides` and `label_extra`. Synthetic District/Metric/Rank/Share
configuration worked through direct Python, while run-spec retained Rows for
Share and omitted Rank's worksheet instance. This predates the text-chart patch,
but left API parity incomplete. Reviewer requested forwarding both options and
a run-spec regression. Parent subsequently reported a separate SDK correction;
WW43 remains on released a1 and this integration did not modify the SDK.

## WW43 evidence checked by the reviewer

- Frozen workbook SHA256 remained
  `83893921f3dbaa372e88baa3a82f3027e352f1828ddbab242d63efa10fedc379`.
- XSD, all 27 SQL/Decimal scenarios, and six negative contract checks passed.
  Reviewer redirected local reports to temporary storage.
- Saved Cloud evidence hashes matched their files.
- Default, June, and Copiers exports matched raw-data oracle and author Data
  exports within currency rounding: 48, 1, and 32 distinct trend months.
- June retained rolling average 28,846.25 rather than incorrectly resetting to
  June sales 34,595.13.
- All exported bar values matched. Default showed 17 categories; June showed 16
  because Copiers has no June sales. No missing-category-label defect confirmed.
- Reviewer inspected six images and found no confirmed business-answer or
  readability blocker. No confirmed WW43 numerical defect.

## Objections retained

- Dashboard interactions were UNVERIFIED. Parameter injection does not establish
  drag selection, min/max aggregation, clear, repeated zoom, multi-select or reset.
  `browser_interaction_executed: false` remains correct.
- Copiers REST filtering directly filters Bars too. Its single-bar render neither
  proves nor disproves the contract that selecting Bars leaves all bars available.
- Copiers observed marks agreed, but the author CSV came from its development
  Data sheet, not Chart. This does not exhaustively establish dashboard
  densification. Machines runtime coverage was outstanding at review time.
- Corpus, final SDK suite, and metadata/catalogue integration were parent gates.
- The reviewer additionally passed 20 focused SDK tests and synthetic text checks
  (rich labels, filters, Measure Values, nested metadata, saved XSD and MCP schema).
- Reviewer explicitly said the requested gpt-6-astra review requirement was unmet
  because it used gpt-6.1-sol. This statement is preserved as a reviewer limitation,
  not recast as having performed a second-model review it did not perform.

## Integration addendum, 2026-10-28

Current saved exports add Machines. `verify_runtime_exports.py` verifies all
12 CSV hashes, eight image hashes and the frozen workbook hash before comparing
four states with the raw-row oracle and the author's Data sheet. Machines has
**39 observed months**, with every exported Sales/Rolling Average value agreeing
within display rounding. Its first three observed months are March, April and
June 2018; the June rolling average is 8,764.80 over those observed marks.

This closes the bounded Machines-export coverage item, not exhaustive dashboard
densification or native action behavior. Category REST filters still affect Bars.

The integration agent inspected the current four replica images and the author
default/Machines images. Different colors, axis text/ticks, title typography,
panel proportions and numeric bar labels are acceptable style differences.
All replica category names are readable, and default shows all 17 categories.
Visual status is **acceptable_delta**, functional status remains **partial**.
