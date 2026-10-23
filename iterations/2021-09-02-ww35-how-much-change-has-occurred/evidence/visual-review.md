# WW35 Cloud/Desktop acceptance — how much change has occurred?

Status: **local gates pass; Desktop and Cloud gates still pending** (coordinator
runs them serially). SDK `23b1df0` (0.29.0a1).

The challenge (Luke Stanke, built by Donna Coles) shows, per Sub-Category, a grey
2020 bar with a coloured 2021 dot on top, the 2021 value as a discrete pill, and
the signed % change as a label. Rows are ordered by 2021 Sales descending.

## What the local gates already checked

- **Data**: the locked extract is `Orders` only (9,994 rows, 2018–2021, 17
  Sub-Categories). The verifier recomputes 2020 Sales, 2021 Sales and
  `% Difference` from the Hyper file, never from the workbook.
- **Author reference**: the printed 2021 pill values and the 2020 dot positions
  from the author's published screenshot are reproduced for all 15 visible rows
  (plus the remaining two from the extract). The dot positions were read back
  through a fitted pixel scale `x = 407.35 + 0.002994 × sales` that reproduces
  every dot centre within 2 px.
- **Window**: a *context* categorical filter on `YEAR(Order Date)` with members
  `2020`/`2021`, also present in `<slices>`; the extract still holds 2018–2021,
  so the window is observable.
- **LoDs**: `2021 Sales` and `2020 Sales` are `{FIXED [Sub-Category]: SUM(IF
  YEAR([Order Date])=… THEN [Sales] END)}`; `% Difference` is the signed relative
  change with the `+0%;-0%` format.
- **Order**: computed sort on `Sub-Category` by `SUM(2021 Sales)` DESC, from
  `Phones` down to `Fasteners`.
- **Panes**: two panes on one synchronised folded column axis bound to
  `SUM(Sales)`; `Circle` above `Bar`, bar pane at `x-index="1"`.
- **Labels and colour**: only the circle pane labels `% Difference`; circle
  colours by `YEAR(Order Date (copy))` (2021 `#4e79a7`, 2020 `#e15759`) with a
  white stroke; bar colours by `YEAR(Order Date)` (2021 `#bab0ac` drawn on top,
  2020 `#e15759`).
- **Layout**: 700×800 fixed dashboard with the challenge author, week and URL.

## Author anomaly recorded, not copied

The author's published raster prints each `% Difference` label **one row below**
its own mark from the second row onwards (13 of the 14 shifted labels match the
next row exactly). The author's workbook XML attaches a single
`<text column="…% Difference…">` encoding to the circle pane with no per-row
offset, so the workbook is correct and only the exported image is misaligned.
The verifier pins the extract to the unaffected values (printed 2021 pills, 2020
dot positions) and compares the published label *sequence* with the documented
one-row shift.

## Expected visual differences (to confirm on the Cloud capture)

- Fonts, bar width, paddings and the scrollbar differ.
- The replica credits `RECREATED WITH : cwtwb` instead of the author.
- Label placement uses Tableau's range-scoped label on the 2021 dot rather than a
  hand-placed annotation.

## Not yet claimed

No Desktop load verdict and no Cloud capture exist for this case yet.
`verification_status` stays `pending`, `functional_status` stays `partial` and
`visual_status` stays `not_evaluated` until the coordinator runs:

```bash
python scripts/desktop/build_and_check.py iterations/2021-09-02-ww35-how-much-change-has-occurred
python scripts/desktop/verify_corpus.py
python scripts/capture_case_cloud.py iterations/2021-09-02-ww35-how-much-change-has-occurred/evidence/cloud-request.json
```
