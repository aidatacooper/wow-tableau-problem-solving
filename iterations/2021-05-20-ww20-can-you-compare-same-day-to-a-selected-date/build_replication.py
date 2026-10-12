"""Rebuild the WW20 "compare same day to a selected date" dashboard.

The challenge (Lorna Brown, built by Donna Coles) compares a user-selected day's
sales against the sales of the *equivalent weekday* one year / one month / one
week earlier, with no LoDs (the author's own solution used none at all).

Chain:
  data (Order Date, Sales)
  → pSelectedDate (date) and pComparison (1|2|3)
  → Exact Date Prev Month, DoW Selected Date, Prior DoW Prev Mth,
    Next DoW Prev Month, Equivalent Day Last Month
  → Equivalent Day Last Year (leap-year aware) and Compare Date
  → Selected Date Sales / Compared Date Sales / % Difference / Dates To Show
  → BAN (MIN(1) bar, fixed 0..1 axis, coloured by % Difference)
  → Chart (Sales by exact Order Date with Selected / Compared / Minus 500 on a
    shared second axis and the value label pinned to the -500 points)
  → Reset button sheet
  → dashboard parameter actions (chart click, reset) plus the True→False
    "Don't highlight" filter action
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/Orders (Sample - Superstore).hyper"
DASHBOARD = "2021_05_19_WW20_Date_Compare"

# Author's BAN palette: a 24-swatch diverging ramp from teal to black.
BAN_COLORS = [
    "#0b8376", "#178a7e", "#249286", "#339a8f", "#43a298", "#55aaa0",
    "#67b1a9", "#7bb9b3", "#91c1bc", "#a7c9c5", "#bfd1cf", "#d9d9d9",
    "#c5c5c5", "#b1b1b1", "#9d9d9d", "#8a8a8a", "#767676", "#626262",
    "#4e4e4e", "#3b3b3b", "#272727", "#131313", "#000000", "#000000",
]

# The equivalent-day logic from the article, kept verbatim so the verifier can
# assert on it.
PRIOR_DOW_CASE = (
    "DATE(CASE [DoW Selected Date]\n"
    "WHEN 1 THEN DATETRUNC('week', [Exact Date Prev Month],'Sunday')\n"
    "WHEN 2 THEN DATETRUNC('week', [Exact Date Prev Month],'Monday')\n"
    "WHEN 3 THEN DATETRUNC('week', [Exact Date Prev Month],'Tuesday')\n"
    "WHEN 4 THEN DATETRUNC('week', [Exact Date Prev Month],'Wednesday')\n"
    "WHEN 5 THEN DATETRUNC('week', [Exact Date Prev Month],'Thursday')\n"
    "WHEN 6 THEN DATETRUNC('week', [Exact Date Prev Month],'Friday')\n"
    "WHEN 7 THEN DATETRUNC('week', [Exact Date Prev Month],'Saturday')\n"
    "END)"
)
EQUIVALENT_LAST_YEAR = (
    "DATE(IF ((DATEPART('month',[pSelectedDate]) <=2) AND "
    "((YEAR([pSelectedDate])-1)%4=0))\n"
    "OR ((DATEPART('month',[pSelectedDate])>=3) AND "
    "(YEAR([pSelectedDate])%4=0))\n"
    "THEN DATEADD('day',2,DATEADD('year',-1,[pSelectedDate]))\n"
    "ELSE DATEADD('day',1,DATEADD('year',-1,[pSelectedDate]))\n"
    "END)"
)
COMPARE_DATE = (
    "DATE(IF [pComparison] = 1 THEN [Equivalent Day Last Year]\n"
    "ELSEIF [pComparison] = 2 THEN [Equivalent Day Last Month]\n"
    "ELSE DATEADD('week', -1, [pSelectedDate])\n"
    "END)"
)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Parameters ---------------------------------------------------------
    editor.add_parameter(
        "pSelectedDate",
        datatype="date",
        default_value="#2021-05-18#",
        domain_type="any",
    )
    editor.add_parameter(
        "pComparison",
        datatype="integer",
        default_value="1",
        domain_type="list",
        allowed_values=["1", "2", "3"],
        allowed_aliases={
            "1": "Same Day Last Year",
            "2": "Same Day Last Month",
            "3": "Last Week",
        },
    )

    # --- Equivalent-day chain ----------------------------------------------
    editor.add_calculated_field(
        "Exact Date Prev Month",
        "DATE(DATEADD('month', -1, [pSelectedDate]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "DoW Selected Date",
        "DATEPART('weekday',[pSelectedDate],'Sunday')",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Prior DoW Prev Mth",
        PRIOR_DOW_CASE,
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Next DoW Prev Month",
        "DATE(DATEADD('week', 1, [Prior DoW Prev Mth]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Equivalent Day Last Month",
        "IF  MONTH([pSelectedDate]) = MONTH([Next DoW Prev Month]) "
        "THEN [Prior DoW Prev Mth]\nELSE [Next DoW Prev Month]\nEND",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Equivalent Day Last Year",
        EQUIVALENT_LAST_YEAR,
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Compare Date",
        COMPARE_DATE,
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dddd, d mmmm yyyy",
    )

    # --- Per-day sales, difference and range -------------------------------
    editor.add_calculated_field(
        "Selected Date Sales",
        "IF [Order Date] = [pSelectedDate] THEN [Sales] END",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "Compared Date Sales",
        "IF [Order Date] = [Compare Date] THEN [Sales] END",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "% Difference",
        "(SUM([Selected Date Sales]) - SUM([Compared Date Sales]))"
        " / SUM([Compared Date Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*▲0.0%;▼0.0%",
    )
    editor.add_calculated_field(
        "Selected Date",
        "[pSelectedDate]",
        datatype="date",
        role="dimension",
        field_type="ordinal",
        default_format="*dddd, d mmmm yyyy",
    )
    editor.add_calculated_field(
        "Dates To Show",
        "[Order Date]>=[Compare Date] AND [Order Date]<=[pSelectedDate]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Minus 500",
        "IF [Order Date] = [pSelectedDate] OR [Order Date]= [Compare Date] "
        "THEN -500 END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Selected | Compared Sales Value",
        "IF [Order Date] = [pSelectedDate] THEN ([Selected Date Sales])\n"
        "ELSEIF [Order Date] = [Compare Date] THEN ([Compared Date Sales])\n"
        "END",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "MIN(1)",
        "MIN(1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    # Constants for the "Don't highlight" True→False filter action.
    editor.add_calculated_field(
        "True", "True", datatype="boolean", role="dimension", field_type="nominal"
    )
    editor.add_calculated_field(
        "False", "False", datatype="boolean", role="dimension", field_type="nominal"
    )
    # Reset sheet.
    editor.add_calculated_field(
        "Reset Label",
        "'Reset'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Default Date",
        "DATE(#2021-05-18#)",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )

    editor.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Compare Date", "*dddd, d mmmm yyyy")
    editor.set_field_format("Selected Date", "*dddd, d mmmm yyyy")

    # --- BAN ----------------------------------------------------------------
    editor.add_worksheet("BAN")
    editor.configure_chart(
        "BAN",
        mark_type="Bar",
        columns=["MIN(1)"],
        color="% Difference",
        label="% Difference",
        label_extra=[
            "EXACTDATE(Selected Date)",
            "Selected Date Sales",
            "Compared Date Sales",
            "EXACTDATE(Compare Date)",
        ],
        label_runs=[
            {"field": "EXACTDATE(Selected Date)", "fontsize": 10},
            {"text": "\n"},
            {"field": "Selected Date Sales", "fontsize": 11},
            {"text": "\n"},
            {"field": "% Difference", "fontsize": 11},
            {"text": "\n"},
            {"text": "vs.", "fontsize": 8},
            {"field": "Compared Date Sales", "fontsize": 8},
            {"text": "\n"},
            {"text": "(", "fontsize": 8},
            {"param": "pComparison"},
            {"text": ": ", "fontsize": 8},
            {"field": "EXACTDATE(Compare Date)", "fontsize": 8},
            {"text": ")", "fontsize": 8},
        ],
        axis_fixed_range={"field": "MIN(1)", "min": 0, "max": 1, "scope": "cols"},
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        "BAN",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        color_style={
            "field": "% Difference",
            "colors": BAN_COLORS,
            "center": 0.0,
            "min": -1.0,
            "max": 1.0,
            "num_steps": 2,
            "reverse": True,
        },
        label_formats=[{"field": "MIN(1)", "display": "false"}],
    )

    # --- Chart --------------------------------------------------------------
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["EXACTDATE(Order Date)"],
        rows=["SUM(Sales)", "Multiple Values"],
        axis_shelf="rows",
        fold_axes=True,
        synchronized=True,
        filters=[{"column": "Dates To Show", "values": [True]}],
        panes=[
            {
                "axis": "SUM(Sales)",
                "mark_type": "Line",
                "detail_extra": ["True", "False"],
                "tooltip": ["EXACTDATE(Order Date)", "SUM(Sales)"],
                "mark_style": {"size": "0.01", "mark-labels-show": "false"},
            },
            {
                "axis": "Multiple Values",
                "mark_type": "Circle",
                "measure_values": [
                    "Selected Date Sales",
                    "Compared Date Sales",
                    "AVG(Minus 500)",
                ],
                "label": "Selected | Compared Sales Value",
                "color": "Measure Names",
                "color_map": {
                    "AVG(Minus 500)": "#ffffff",
                    "Selected Date Sales": "#f28e2b",
                    "Compared Date Sales": "#e15759",
                },
                "detail_extra": ["True", "False"],
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "range",
                    "mark-labels-range-scope": "table",
                    "mark-labels-range-field": "Measure Names",
                    "mark-labels-range-min": "true",
                    "mark-labels-range-max": "false",
                    "size": "1.087458610534668",
                },
                "tooltip": [
                    "EXACTDATE(Order Date)",
                    "Selected | Compared Sales Value",
                ],
            },
        ],
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        pane_datalabel_style={"font-size": "8"},
        axis_style={
            "per_field": [
                {
                    "field": "SUM(Sales)",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "SUM(Sales)",
                    "scope": "rows",
                    "attr": "title",
                    "value": "",
                },
                {
                    "field": "Multiple Values",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "Multiple Values",
                    "scope": "rows",
                    "attr": "title",
                    "value": "",
                },
                {
                    "field": "EXACTDATE(Order Date)",
                    "scope": "cols",
                    "attr": "display",
                    "value": "false",
                },
            ]
        },
    )

    # --- Reset --------------------------------------------------------------
    editor.add_worksheet("Reset")
    editor.configure_chart(
        "Reset",
        mark_type="Square",
        label="Reset Label",
        detail="Default Date",
        tooltip=[],
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        "Reset",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_mark_style={
            "mark-color": "#000000",
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
            "size": "14.547999382019043",
        },
    )

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 500 * 100000),
            "y": round(y / 600 * 100000),
            "w": round(w / 500 * 100000),
            "h": round(h / 600 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {"text": "Can you compare ", "font_size": "14"},
                {"param": "pComparison", "font_size": "14", "bold": True},
                {"text": " based on a ", "font_size": "14"},
                {
                    "text": "Selected Date",
                    "font_size": "14",
                    "bold": True,
                    "font_color": "#0000ff",
                },
                {"text": "?", "font_size": "14"},
            ],
            "absolute": pos(8, 8, 484, 42),
        },
        {
            "type": "paramctrl",
            "parameter": "pSelectedDate",
            "mode": "datetime",
            "caption": "Select a Date",
            "absolute": pos(8, 58, 150, 66),
        },
        {
            "type": "paramctrl",
            "parameter": "pComparison",
            "mode": "list",
            "caption": "Select Comparison",
            "absolute": pos(160, 58, 190, 66),
        },
        {
            "type": "worksheet",
            "name": "BAN",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 130, 484, 130),
        },
        {
            "type": "worksheet",
            "name": "Reset",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 266, 150, 30),
        },
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 300, 484, 250),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "CHALLENGE BY LORNA BROWN",
                    "font_size": "8",
                    "font_color": "#000000",
                    "font_alignment": "0",
                }
            ],
            "absolute": pos(8, 556, 161, 20),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021  |  WEEK 20",
                    "font_size": "8",
                    "font_color": "#000000",
                    "font_alignment": "1",
                }
            ],
            "absolute": pos(169, 556, 162, 20),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "RECREATED BY DONNA COLES",
                    "font_size": "8",
                    "font_color": "#000000",
                    "font_alignment": "2",
                }
            ],
            "absolute": pos(331, 556, 161, 20),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=500,
        height=600,
        layout={
            "type": "container",
            "direction": "floating",
            "children": children,
        },
        worksheet_names=["BAN", "Chart", "Reset"],
    )

    # Clicking a point on the line chart selects the date.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Chart",
        source_field="Order Date",
        target_parameter="pSelectedDate",
        aggregation="attr",
        caption="Set Date",
    )
    # The reset button sets the date back to 18 May 2021.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Reset",
        source_field="Default Date",
        target_parameter="pSelectedDate",
        aggregation="attr",
        caption="Reset",
    )
    # Map True -> False so the click never leaves a selection highlight behind.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Chart",
        target_sheet="Chart",
        field_mappings={"True": "False"},
        caption="Don't highlight",
    )

    for name in ("BAN", "Chart", "Reset"):
        editor.set_worksheet_title(name, "")
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
