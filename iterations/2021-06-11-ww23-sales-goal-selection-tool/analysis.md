# Analysis: 2021 Week 23 — Sales Goal Selection Tool

- Article: <https://donnacoles.home.blog/2021/06/11/sales-goal-selection-tool/>
- Challenge: <https://www.workout-wednesday.com/2021w23tab/> (Ann Jackson, 2021-06-09)
- Author workbook: `dashboards/2021_06_09_WW23_Sales_Goal_Selection/2021_06_09_WW23_Sales_Goal_Selection.twbx`
- Extract: `inputs/TEMP_15y4ojb1ek80451dcvfe90xwheay.hyper`
  (`Order Date`, `Category`, `Sub-Category`, `Sales`; 9,994 rows, 2018-01-03 → 2021-12-30)

## Business question

The dashboard users had two ways to compute a year-end sales goal and wanted to
choose per sub-category, then aggregate the *mixed* goals into one headline
number. The challenge is therefore as much about the goal arithmetic as about
the set-action toggle that switches a sub-category between the two methods.

## The two goal methodologies

`pToday` is fixed to 2021-06-09 and `pPercentIncrease` defaults to 10%.

- **Same pace** — extrapolate this year's run-rate:
  `(SUM([SALES YTD by Sub Cat]) / [# Days So Far This Year]) * [# Days In Year]`.
  Both day counts are `DATEDIFF` based (`DATETRUNC('year', ...)` →
  `DATEADD('year', 1, ...)`) so leap years stay correct.
- **Last year + X%** — `SUM([SALES LY]) * (1 + [pPercentIncrease])`, where
  `SALES LY` is the whole of 2020 and `SALES LY YTD by Sub Cat` is the
  comparable 1 Jan – 9 Jun 2020 window.

The per-row goal switches on set membership:

```
YEAR-END GOAL Per Sub Cat =
  IF ATTR([Use Last Year With Increase]) THEN [LY + Percent Increase Goal]
  ELSE [Same Pace Goal] END
```

`Value to Goal = goal - SALES YTD`, `% of Goal = SALES YTD / goal`.

## The aggregation subtlety

The column grand total of `YEAR-END GOAL Per Sub Cat` is *not* the number the
users want: it evaluates `ATTR` across the whole table and picks one branch.
The author solves this with window table calcs over the displayed rows
(`SALES YTD = WINDOW_SUM(SUM([SALES YTD by Sub Cat]))`, likewise
`SALES LY YTD` and `YEAR-END GOAL = WINDOW_SUM([YEAR-END GOAL Per Sub Cat])`),
plus `Index = INDEX()` filtered to `<= 1` so exactly one row is displayed while
the window still spans all 17 sub-categories.

## The toggle

`Use Last Year With Increase` is a set on `Sub-Category`, seeded in the author's
workbook with `Accessories`, `Copiers`, `Machines`, `Phones`. Two
`edit-group-action` set actions drive it:

- **Add to Set** — `on-select`, `add`, `do-nothing` clear: clicking a bar
  (or circle) puts that sub-category on the "last year + %" method.
- **TOGGLE TYPE** — the tooltip's action name, `remove`, `do-nothing` clear:
  clicking the link in the tooltip takes it back off.

The article describes the second action as running "on select" but the author's
workbook serializes it as `explicit` (menu/tooltip), which is what the replica
uses.

## The chart

One worksheet with five panes sharing a folded column axis:

| column | mark | encodings |
| --- | --- | --- |
| `Multiple Values` | Bar | `Measure Names` on Colour **and** Size; tooltips for SALES YTD / SALES LY YTD / goal |
| `YEAR-END GOAL Per Sub Cat` | GanttBar | black goal tick |
| `Value to Goal` | Text | `MIN(0)` axis, label `<Value to Goal> to goal` |
| `% of Goal` | Text | `MIN(0)` axis, label `<% of Goal> of goal` |
| `MIN(0)` (2nd copy) | Circle | colour by `Use Last Year With Increase` (`#a4a4d5` in / `#91dcea` out) |

`MIN(0)` columns are the author's invisible anchor that gives the text and
circle panes their own place on the axis. Stack marks are off (bars overlay),
`Measure Names` drives both size and colour, and the y-axis is a continuous
`Category / Sub-Category` pair with the Category header rotated -90°.

## Layout

1200×800 fixed dashboard: title text ("SALES GOAL SELECTION TOOL" / "CLICK
BUTTON TO TOGGLE GOAL CALCULATION"), the BAN strip, the chart, and a footer with
the challenge credit and the two-colour legend.

## Numbers (independently recomputed from the locked extract)

| headline | value |
| --- | --- |
| SALES YTD | $216,042 |
| SALES LY YTD | $199,947 |
| YEAR-END GOAL | $546,803 |

`YEAR-END GOAL` with the author's four-member set = $546,803; the same
calculation with only `Phones` selected gives the $513,833 shown in the
article's mid-build screenshot, and with no members it gives $492,845 — the
same-pace total. That progression is the strongest evidence the mixed-goal
aggregation is implemented correctly.

## cwtwb notes

- `add_set` writes a native `<group>` with the four member `<groupfilter>`s.
- `add_dashboard_set_action(selection_mode="add"/"remove", clear_option="do-nothing")`
  emits the two `edit-group-action` elements, including the
  `GroupActionAddRemove` / `SetMembershipControl` manifest entries.
- `configure_layered_chart` with five panes and `axis_shelf="columns"` +
  `fold_axes=True` reproduces the multi-pane, shared-axis layout.
- `add_parameter`'s `[Parameters].[Parameter N]` reference is normalized by the
  verifier; no raw XML is used anywhere in the builder.
