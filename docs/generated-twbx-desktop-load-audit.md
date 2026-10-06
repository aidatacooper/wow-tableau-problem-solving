# Generated TWBX Desktop-load audit

Date: 2026-10-06
Scope: all `iterations/*/outputs/replicated-workbook.twbx` in this repository
Verdict: **51 of 90 committed artifacts failed Tableau's own TWB XSD and could
not be opened in Tableau Desktop.** The acceptance pipeline never opened a
packaged workbook, so these passed as `functional_status: replicated` /
`cwtwb_result: pass`.

All 23 active cases affected are now schema-clean and rebuilt. Desktop
spot-checks confirm several previously unopenable workbooks now load; the
remaining ones have a second, non-schema defect that predates this work (see
sections 6 and 8).

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

All 23 active cases with strict errors are now schema-clean and rebuilt. The
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

* Cases that now open: `2019-07-25-ww30-navigation-kpi`,
  `2020-03-13-ww11-smart-ranked-lists`, `2020-05-08-ww19-dynamic-date-drilling`,
  `2023-11-30-ww48-bars-and-candlesticks`, plus `2026-02-15-ww06-null-safe-averages`
  and `2026-03-01-ww08-dzv-filter-actions` from the earlier change set.
* Cases that are schema-clean but still fail to load (for example
  `2019-08-04-ww31-hub-spoke-map`, `2020-05-15-ww20-state-contribution`):
  bisecting top-level sections did not isolate the cause, and Tableau reports
  only the generic `d2e8da72` code. Their committed versions already failed, so
  this is not a regression from these fixes.
* Rebuilding changes bytes, so Cloud-captured replica hashes in
  `evidence/cloud-verification.json` must be refreshed through the normal
  capture flow rather than patched in place.
* The 4 historical (schema 1.0.0, `verification_status: historical`) cases
  remain read-only by repository policy and were not touched.

### 8.3 Recommended next steps

1. **Add a Desktop smoke test** to CI for cases using actions, parameters or
   table calculations, reusing the log-based classifier in section 7. The XSD
   gate cannot catch non-schema defects.
2. **Localise the remaining non-schema defects.** A useful technique: compare a
   workbook that opens against one that does not, swapping one top-level section
   at a time, then bisect within the section that changes the outcome.
3. **Refresh Cloud evidence** for the rebuilt cases through the capture flow.

## 9. Artifacts

* `cwtwb` PR #7 — schema-derived ordering, style/action/parameter normalisation,
  plus `tests/test_schema_order.py` and `tests/test_xsd_element_order.py`
* `scripts/validate_iteration.py` — XSD gate
* `iterations/2026-02-15-ww06-null-safe-averages/` — first fixed case
* 22 further rebuilt cases listed in section 8.1
* `usage/case-index.json` — regenerated catalogue
