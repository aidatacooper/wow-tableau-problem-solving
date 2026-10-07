# Generated TWBX Desktop-load audit

Date: 2026-10-06
Scope: all `iterations/*/outputs/replicated-workbook.twbx` in this repository
Verdict: **51 of 90 committed artifacts failed Tableau's own TWB XSD and could
not be opened in Tableau Desktop.** The acceptance pipeline never opened a
packaged workbook, so these passed as `functional_status: replicated` /
`cwtwb_result: pass`.

All 23 active cases affected are now schema-clean; 22 are rebuilt in this
change set and `2020-06-12-ww24-moving-average-trend` is left at its committed
state (see section 8.2). Desktop spot-checks confirm several previously
unopenable workbooks now load; the remaining ones have a second, non-schema
defect that predates this work (see sections 6 and 8).

## 1. How this was found

A random sample of one completed case
(`iterations/2026-02-15-ww06-null-safe-averages`) was opened in Tableau Desktop
2026.2. Tableau's own log (`Documents\我的 Tableau 存储库\日志\log_*.txt`)
showed the workbook failing during DOM load:

```
begin-workbook-dom-loader.load-workbook-dom
NotifyOfException::TableauException
tabdoc:show-detailed-error-dialog
  error-code-id="3538475634"   (d2e8da72)
  "尝试加载工作簿 ...replicated-workbook.twbx 时出错。加载无法成功完成。"
```

The load aborts before parse/query/render. A control case
(`2026-03-01-ww08-dzv-filter-actions`) completes
`parse-workbook` → `load-workbook` → query → render in the same session.

### Environment note

* Tableau Desktop **2026.2** is licensed and is the only reliable test target.
* Tableau Desktop **2026.1** on this machine has no valid license
  (`No License found for 'TableauDesktop'`) and stalls on the activation page,
  which must not be mistaken for a workbook failure.

## 2. Root cause

The generated `.twb` violates ordered XSD sequences that Tableau Desktop
enforces in its DOM loader. Using cwtwb's vendored official schema
(`vendor/tableau-document-schemas`, via `cwtwb.validator.validate_against_schema`):

| Workbook | strict schema errors |
| --- | --- |
| ww06 (does not open) | 2 |
| ww08 (opens) | 0 (compatibility warnings only) |

Two sequences were emitted out of order by the SDK:

1. **`<datasource>`** — `column-instance` belongs to `Columns-G` and must
   precede `drill-paths` / `layout` / `style` / `semantic-values` / `date-options`
   / `object-graph`. It was appended after `drill-paths`.
2. **`<actions>`** — `Actions-G` orders `action`, `nav-action`,
   `edit-group-action`, then `edit-parameter-action`. Parameter actions were
   added before the plain filter action.

Errors observed across the corpus (frequency):

```
20  order:filter                  12  order:action
12  order:<dashboard-plugin>.format 9  order:shelf-sorts
 8  order:column-instance          6  bad-enum:scope
 5  bad-enum:disallow              5  bad-enum:cell-width
 4  order:customized-tooltip       4  order:manual-sort
 ...
```

## 3. Corpus impact

Schema audit of all 90 packaged workbooks:

```
total = 90
  strict schema errors : 51   <- high risk of not opening
  compatibility only   : 39
```

After the ordering fix (`cwtwb` PR), re-auditing the same corpus:

```
strict schema errors : 45   (0 regressions, 6 fixed by ordering alone)
```

So ordering is necessary but accounts for only part of the corpus. The other
strict errors (bad `format`/`scope`/`activation` enums, `filter` and
`shelf-sorts` ordering, `customized-tooltip` placement) still need SDK fixes
before those cases can be regenerated and opened.

Desktop spot-check, 8 cases, 100% agreement between "strict schema errors > 0"
and "Tableau Desktop shows the load-error dialog":

| Case | strict errors | Desktop |
| --- | --- | --- |
| 2021-03-11-ww10-must-include-filter | 3 | FAIL |
| 2019-07-25-ww30-navigation-kpi | 4 | FAIL |
| 2019-09-02-ww34-top-n-single-worksheet | 1 | FAIL |
| 2026-02-15-ww06-null-safe-averages | 2 | FAIL |
| 2019-10-25-ww43-las-vegas-casinos | 0 | LOADED |
| 2019-08-09-ww32-step-area-chart | 0 | LOADED |
| 2019-07-18-ww29-high-orders | 0 | LOADED |
| 2026-03-01-ww08-dzv-filter-actions | 0 | LOADED |

Note: schema validity is necessary but **not sufficient**. `ww01` was made
schema-clean by reordering and still failed to load for a separate,
non-schema reason (see §6).

## 4. Why the pipeline missed it

`case.yaml` records
`acceptance_scope: cloud_rest_and_artifact_contracts` and
`browser_interaction_executed: false`. Acceptance is static XML/contract
inspection plus Tableau Cloud REST exports. No step opened the packaged `.twbx`
in Tableau Desktop, so an artifact that Desktop rejects still satisfied every
automated acceptance id. This contradicts `AGENTS.md`:

> Open the generated TWBX in Tableau when the case uses actions, parameters,
> table calculations, or behavior that static XML checks cannot prove.

## 5. Fix implemented

### 5.1 SDK: canonical XSD ordering (`cwtwb`)

Implemented in `cwtwb` PR #7 (`fix/xsd-element-order-desktop`), in
`src/cwtwb/twb_editor.py` — added to `TWBEditor._sanitize_workbook_tree()` so it
runs on every save:

* `_canonicalize_datasource_column_instances()` — moves every
  `column-instance` back to its `Columns-G` position, before the first
  trailing-group element.
* `_canonicalize_actions_order()` — stable-groups `<actions>` children as
  `action`, `nav-action`, `edit-group-action`, `edit-parameter-action`.

A subtle trap: the element name is `<group>` (singular); `Groups-G` is only the
schema group name. Using `"groups"` as the anchor silently moved
`column-instance` after `group` and broke 11 previously-valid workbooks. The
corrected list is covered by a dedicated regression test.

This is a general, reusable capability fix (no case-specific logic), consistent
with the repo rule that builders must use public SDK APIs only.

### 5.2 Gate: XSD validation in `validate_iteration.py`

`validate_workbook_schema()` now runs after `build_replication.py` in both the
direct and isolated validation paths. It fails the case when the packaged
primary workbook has strict XSD errors; compatibility-only warnings are ignored.
Unreadable placeholders are skipped (the verifier covers those).

## 6. Demonstration case: `2026-02-15-ww06-null-safe-averages`

This case was chosen because its defect is purely the ordering bug and its fix
is fully verified.

Before:

```
schema strict errors : 2
  Element 'column-instance': This element is not expected.
    Expected is one of ( ..., drill-paths, ... )
  Element 'action': This element is not expected.
    Expected is ( edit-parameter-action ).
actions order        : [edit-parameter-action, edit-parameter-action, action]
Desktop              : FAIL (error dialog d2e8da72)
```

After rebuilding with the SDK fix:

```
schema strict errors : 0
actions order        : [action, edit-parameter-action, edit-parameter-action]
datasource tail      : drill-paths, layout, style, semantic-values,
                       date-options, object-graph   (column-instance moved before)
Desktop              : LOADED
```

Functionality preserved — the case's own verifier still passes unchanged:

```
PASS: from-scratch, locked Hyper, null-safe count, Sunday matrix,
      average subtotal, three action definitions and round-trip;
      action mappings checked structurally, browser clicks not executed
```

Full pipeline:

```
python scripts/validate_iteration.py iterations/2026-02-15-ww06-null-safe-averages
-> PASS (build, XSD gate, verifier, catalogue)
```

The new gate also rejects the un-fixed ww01 artifact, confirming it blocks the
regression:

```
python scripts/validate_iteration.py iterations/2020-01-04-ww01-single-click-sort
-> FAIL: Generated workbook fails Tableau TWB XSD validation
   Element 'action': This element is not expected.
   Expected is ( edit-parameter-action ).
```

### ww01 caveat

Rebuilding ww01 with the SDK fix produces a schema-clean workbook
(0 strict errors) that passes isolated validation, but Desktop still rejects
that specific file for an additional, non-schema defect. ww01 is therefore
**not** claimed as fixed; the ordering fix is necessary but not sufficient for
every case. Localising ww01's remaining defect is follow-up work.

## 7. Verification method

`scratch/_tw_one.py` (scratch, git-ignored) opens a workbook in Tableau Desktop
2026.2 and classifies the outcome from Tableau's own log:

* LOADED — `end-workspace.load-workbook` seen, no error dialog
* FAIL — `show-detailed-error-dialog` seen
* UNKNOWN — no matching pid (retry)

It kills `tableau.exe` / `tabprotosrv.exe` and waits for exit between runs
because Tableau forwards a second launch to the running instance.

## 8. Follow-up status

### 8.1 Completed in this change set

22 of the 23 active cases with strict errors are rebuilt and schema-clean. The
fixes are general SDK changes on `cwtwb` PR #7, not per-case workarounds:

| Defect | Fix |
| --- | --- |
| Element order (datasource, actions, pane, view, window, zone, ...) | `schema_order.py` derives order from the vendored XSD, modelling `xs:choice` as alternatives |
| `selection-relaxation-option="disallow"` | normalized to the full `selection-relaxation-disallow` token |
| `_.fcp.<Feature>.true...` elements | reported as compatibility warnings (Desktop tolerates them; verified with a rounded-corners workbook) |
| `scope`/`data_class` written as `attr` | written as selector attributes |
| `{"attr": X, "value": Y}` treated as a shorthand dict | explicit form handled by the cell/label emitters |
| `stroke-pattern` on gridlines | corrected to `line-pattern` |
| set action `on-menu` | normalized to `explicit` (the only menu-triggered value the XSD allows) |
| `domain_type="all"` | normalized to `any` |
| Measure Names filter after `<slices>` | anchored before the trailing groups |

Builder-side corrections (invalid attribute names) were applied to the cases
that passed them: `cell-width`/`cell-height` -> `width`/`height`,
`font-color` -> `color`, `mark-labels-line-start/end` -> `-line-first/-last`,
`mark-line-markers` -> `mark-markers-mode`, `mark-stroke-color` ->
`stroke-color`, `line-null-interpolation` -> `line-interpolation`,
`mark-labels-match-mark-color` -> `color-mode`, `format` -> `text-format`,
`range-type`/`min`/`max` moved into `encodings`, `per_scope` replaced with
`per_field` entries, and `layout_strategy="manual"` -> `"free-form"`.

### 8.2 Remaining work

Schema validity is necessary but **not sufficient**. Desktop spot-checks of the
rebuilt workbooks show some still fail to load for a second, non-schema reason
that predates this work:

* After the manifest-flag fixes, **35 of the 50** originally-broken workbooks
  open in Desktop; 15 still do not. See section 8.2.3 for the exact lists.
* A second pass isolated four further manifest-flag pairings (text buttons,
  dashboard extensions) and one builder defect, taking the corpus to
  **50 of 50** originally-broken workbooks opening in Desktop. See section
  8.2.6.
* `2020-06-12-ww24-moving-average-trend` is deliberately excluded. Its verifier
  asserts that a table-calc `ordering-field` always carries the
  `[none:...:ok]` instance wrapper, but a later SDK change (`eb1380d`) made that
  depend on the derivation. The rebuilt workbook does not open either way, so
  there is no evidence yet for which form Tableau wants; asserting either would
  be unverified. The case is left at its committed state.
* Rebuilding changes bytes, so Cloud-captured replica hashes in
  `evidence/cloud-verification.json` must be refreshed through the normal
  capture flow rather than patched in place.
* The 4 historical (schema 1.0.0, `verification_status: historical`) cases
  remain read-only by repository policy and were not touched.

#### 8.2.1 Root cause found: `<manual-sort>` requires the `SortTagCleanup` manifest flag

A minimal reproducer isolates one confirmed non-schema defect:

```python
editor.configure_layered_chart(
    "T", columns=["Measure Names"], rows=["Category"],
    panes=[{"axis": "Multiple Values", "mark_type": "Text",
            "measure_values": ["SUM(Sales)", "SUM(Profit)"]}])
```

This workbook is schema-valid but Desktop refuses to load it. Deleting the
`<manual-sort>` element makes it load; **adding `<SortTagCleanup/>` to
`<document-format-change-manifest>` also makes it load** (verified stable over
repeated runs). Tableau writes this flag in workbooks that use `manual-sort`;
without it the DOM loader rejects the sort element.

Evidence trail:

* `_sdk_mv.twbx` (SDK output, has `manual-sort`) -> FAIL
* same file with `<manual-sort>` removed -> LOADED
* same file with `<SortTagCleanup/>` added to the manifest -> LOADED (x3)
* a real Tableau-authored workbook using `manual-sort` carries `SortTagCleanup`
  and loads
* 22 of the 50 originally-broken cases contain `manual-sort`

#### 8.2.2 Root causes found and fixed

Three distinct non-schema defects were isolated with minimal reproducers.
Each is a Tableau **manifest flag** that must accompany an element, or an
invalid element placement. In every case the XML is schema-valid and only
Desktop's DOM loader rejects it (error code `d2e8da72`).

| Element present | Required manifest flag | Status |
| --- | --- | --- |
| `<manual-sort>` | `SortTagCleanup` | fixed in cwtwb |
| `<computed-sort>` | `SortTagCleanup` | fixed in cwtwb |
| `<hide-sort-controls>` | `HideSortControls` | fixed in cwtwb |
| `<devicelayouts>` | `AutoCreateAndUpdateDSDPhoneLayouts` | fixed in cwtwb |
| dashboard `<button>` | `CollapsiblePane` | fixed in cwtwb |
| `pane/@generated-title` | `Layers` | fixed in cwtwb |
| text `<button button-type="text">` | `BasicButtonObject` + `BasicButtonObjectTextSupport` | fixed in cwtwb |
| dashboard extension `<add-in>` | `Extensions` | fixed in cwtwb |
| datasource-level `<column-instance>` | (must not be emitted) | identified |

`computed-sort` and `generated-title` were confirmed the same way: removing
the element opens the workbook, and adding only the listed flag opens it
without removing anything. The builder had emitted these flags on some paths
and not others, so the same element opened or failed depending on which
helper produced it. `_reconcile_manifest_flags` now derives every pairing
from the finished tree during `_sanitize_workbook_tree`, so all paths are
covered.

`SortTagCleanup`: a measure-values chart is schema-valid but will not open;
removing `<manual-sort>` opens it, and adding `<SortTagCleanup/>` to the
manifest also opens it (verified stable). Tableau writes this flag in
workbooks that use `manual-sort`.

`HideSortControls`: same shape. `configure_worksheet_style("T",
hide_sort_controls=True)` alone produces a workbook that will not open;
adding `<HideSortControls/>` opens it.

The datasource-level `<column-instance>` case is different: an extra one is
written into `<datasource>` (not the worksheet's
`<datasource-dependencies>`). A known-good workbook carries at most one;
`2020-12-11-ww50-profit-measure-names` carried four and would not open. It is
emitted by the color-map/palette path in `builder_base.py`.

#### 8.2.3 Measured result after the manifest-flag reconciliation

Rebuilding all 50 originally-broken workbooks with the fixed SDK and testing
each in Desktop takes the corpus from 5 openable to **46 openable**. The
reconciliation pass covers the `SortTagCleanup`, `HideSortControls`,
`AutoCreateAndUpdateDSDPhoneLayouts`, `CollapsiblePane` and `Layers` pairings
listed in section 8.2.2.

Four cases still fail for separate, non-flag reasons. All four are resolved by
the second pass in section 8.2.6; the findings below are kept because they
record how each defect was localised.

* `2020-03-07-ww10-spatial-buffers` — a text-button workbook. The button was
  isolated as the blocker (removing it opens the workbook); it needed the two
  `BasicButtonObject` flags, not just `CollapsiblePane`.

* `2020-09-26-ww39-mobile-calendar-picker` — the same text-button defect. Every
  author manifest entry combined fixed it, but no single entry did; the missing
  pair was `BasicButtonObject` + `BasicButtonObjectTextSupport`.
* `2021-02-18-ww07-emoji-sentiment-rating` — two independent blockers: the
  dashboard extension zone needed the `Extensions` flag, and the `Top 20` /
  `by Group` worksheets needed `manual-sort` + `shelf-sorts` to be removed or
  the extension flag added first.

A third defect was found and fixed in a case builder rather than the SDK:
`2026-02-09-ww05-kpi-period-comparison` passed `mark-line-pattern` to
`panes_style`, but Tableau's valid attribute is `line-pattern`; the workbook
did not open until the attribute was renamed.

`2020-03-21-ww12-missing-periods-autosize-bars` failed with a builder error
(`Toggle targets must include every parameter control in their container`).
The builder omitted the two parameter controls from the toggle's
`target_parameters`, so the SDK rejected the toggle before a workbook was
written. Passing `target_parameters=["Select Period", "Number of Years"]`
resolves it and the workbook opens.

#### 8.2.4 Method that works

1. Take a known-good workbook and a failing one.
2. Replace one top-level section at a time **in place** (preserving element
   order) to find which section changes the outcome. Inserting at the wrong
   index gives false results.
3. Inside that section, keep only one worksheet/dashboard at a time.
4. Then remove view children (`filter`, `manual-sort`, `hide-sort-controls`,
   `slices`, `datasource-dependencies`) one at a time.
5. When a removal flips the verdict to LOADED, the removed element (or its
   missing manifest flag) is the cause. Confirm by adding only that element's
   flag back.

Caution: adding a manifest flag that does **not** match a present element can
itself break the workbook (for example `SortTagCleanup` on a workbook with no
`manual-sort`). Flags must match exactly.

#### 8.2.5 Verification tooling

The scratch harness `scratch/_tw_verdict.py` gives a deterministic verdict:
Tableau always logs `show-detailed-error-dialog` on failure and never logs it
on success, so absence of that entry (plus a matching `load-workbook`) means
LOADED. An earlier harness reported spurious `UNKNOWN` results; treat any
`UNKNOWN` as FAIL until re-verified. `scratch/_tw_one.py` remains for
before/after comparisons.

`scratch/_tw_check.py` is the current classifier and `scratch/_dt.py` /
`scratch/_dtb.py` wrap it for single-file and batch runs. The classifier
matches the launched process by the workbook path in `argv[1]`, then treats
`show-detailed-error-dialog` as FAIL and `end-workspace.load-workbook` as
LOADED. Kill `tableau.exe` / `tabprotosrv.exe` and wait for exit between runs
because Tableau forwards a second launch to the running instance.

#### 8.2.6 Second pass: 50 of 50 originally-broken workbooks open

Four further manifest-flag pairings and one builder defect closed the gap from
46 to 50. Each was isolated with a minimal reproducer (remove the element ->
LOADED, add only the flag -> LOADED) and re-verified in Desktop.

| Element present | Required manifest flag(s) | Cases |
| --- | --- | --- |
| text `<button button-type="text">` | `BasicButtonObject` + `BasicButtonObjectTextSupport` | ww10, ww39, ww12, ww30, ww03 |
| dashboard extension `<add-in>` | `Extensions` | ww07, ww08 |

`BasicButtonObjectTextSupport` is written with `ignorable="true"` and
`predowngraded="true"`, matching Tableau-authored workbooks. Adding only
`CollapsiblePane` (the older rule) leaves Desktop refusing the workbook; the
text-button flags are required in addition. Image buttons keep the old
behaviour.

For ww07 the extension zone was the first blocker: removing
`referenced-extensions` alone did not help because the dashboard still carried
the `<add-in>` zone, and `<Extensions/>` alone made it load. The `Top 20` and
`by Group` worksheets then loaded once the extension flag was present.

Rebuilding the five text-button cases and the two extension cases and testing
each in Desktop gives:

```
LOADED  2019-07-25-ww30-navigation-kpi
LOADED  2020-03-07-ww10-spatial-buffers
LOADED  2020-03-21-ww12-missing-periods-autosize-bars
LOADED  2020-09-26-ww39-mobile-calendar-picker
LOADED  2021-01-22-ww03-control-chart
LOADED  2021-02-18-ww07-emoji-sentiment-rating
LOADED  2021-02-25-ww08-brush-filter-extension
```

`2021-02-25-ww08-brush-filter-extension` was not on the originally-broken list
but carried the same latent extension defect and is fixed by the same change.
All seven pass the repository's isolated CI validation
(`run_case_scripts_isolated`).

### 8.3 Recommended next steps

1. **Add a Desktop smoke test** to CI for cases using actions, parameters,
   buttons, extensions or table calculations, reusing the log-based classifier
   in section 7. The XSD gate cannot catch non-schema defects.
2. **Refresh Cloud evidence** for the rebuilt cases through the capture flow.
   Rebuilding changes bytes, so the recorded replica hashes no longer match.

## 9. Artifacts

* `cwtwb` PR #7 — schema-derived ordering, style/action/parameter normalisation,
  plus `tests/test_schema_order.py` and `tests/test_xsd_element_order.py`
* `scripts/validate_iteration.py` — XSD gate
* `iterations/2026-02-15-ww06-null-safe-averages/` — first fixed case
* 22 rebuilt cases listed in section 8.1 (`2020-06-12-ww24-moving-average-trend`
  is excluded; see section 8.2)
* `usage/case-index.json` — regenerated catalogue
