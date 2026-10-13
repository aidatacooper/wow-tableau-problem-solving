"""Rebuild the WW27 "top and bottom performers" dashboard.

The challenge (Candra McRae, built by Donna Coles) flags Sub-Categories in the
top and bottom quartiles of rolling sales, comparing the current rolling N
months against the previous N months. A separate month selector sheet drives the
`pRollingMonth` parameter.

Chain:
  data (Order Date, Sub-Category, Sales)
  → Max Date = DATE({FIXED:MAX([Order Date])})
  → pRollingMonth (integer, default 12)
  → Current Rolling Sales  = sales between DATETRUNC('month',[Max Date])-N months
    and [Max Date]
  → Prev Month = DATEADD('month', -1, [Max Date])
  → Previous Rolling Sales = the same window ending at [Prev Month]
  → Difference = SUM(Current) - SUM(Previous)
  → 25th/75th Percentile = WINDOW_PERCENTILE(SUM([Current Rolling Sales]), .25/.75)
  → Colour = Top / Bottom / Middle by the quartile thresholds
  → Sales Contraction Indicator = '●' when the difference is negative
  → Chart: Sub-Category bars (current rolling sales, coloured by Colour) over a
    Gantt bar (previous rolling sales), with a hidden Sub-Category (copy) row
    carrying the contraction circle
  → Month Selector: MONTH([Order Date]) squares driving pRollingMonth
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_1klgcbl133n11m1cf4c4d17vycpr.hyper"
DASHBOARD = "2021_07_06_WW27_Top_Bottom_Performers"

# The author's quartile palette.
QUARTILE_COLORS = {
    "Top": "#85cecf",
    "Middle": "#dbdbdb",
    "Bottom": "#fb9f8c",
}
CIRCLE_RED = "#e15759"

CURRENT_ROLLING = (
    "IF [Order Date]>= DATEADD('month', -1 * [pRollingMonth] ,"
    "DATETRUNC('month',[Max Date])) AND [Order Date] <= [Max Date] "
    "THEN [Sales] END"
)
PREVIOUS_ROLLING = (
    "IF [Order Date]>= DATEADD('month', -1 * [pRollingMonth] ,"
    "DATETRUNC('month',[Prev Month])) AND [Order Date] <= [Prev Month] "
    "THEN [Sales] END"
)
COLOUR = (
    "IF SUM([Current Rolling Sales]) >= [75th Percentile] THEN 'Top'\n"
    "ELSEIF SUM([Current Rolling Sales]) <= [25th Percentile] THEN 'Bottom'\n"
    "ELSE 'Middle'\n"
    "END"
)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    editor.add_parameter(
        "pRollingMonth",
        datatype="integer",
        default_value="12",
        domain_type="any",
    )

    # --- Rolling-window measures -------------------------------------------
    editor.add_calculated_field(
        "Max Date",
        "DATE({FIXED:MAX([Order Date])})",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Prev Month",
        "DATEADD('month', -1, [Max Date])",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Current Rolling Sales",
        CURRENT_ROLLING,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0,.0K;-"$"#,##0,.0K',
    )
    editor.add_calculated_field(
        "Previous Rolling Sales",
        PREVIOUS_ROLLING,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0,.0K;-"$"#,##0,.0K',
    )
    editor.add_calculated_field(
        "Difference",
        "SUM([Current Rolling Sales]) - SUM([Previous Rolling Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0,.0K;("$"#,##0,.0K)',
    )
    editor.add_calculated_field(
        "Label:Current Rolling Sales",
        "SUM([Current Rolling Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0,.0K;-"$"#,##0,.0K',
    )

    # --- Quartile classification -------------------------------------------
    editor.add_calculated_field(
        "25th Percentile",
        "WINDOW_PERCENTILE(SUM([Current Rolling Sales]),0.25)",
        datatype="real",
        role="measure",
        field_type="quantitative",
        table_calc="Columns",
    )
    editor.add_calculated_field(
        "75th Percentile",
        "WINDOW_PERCENTILE(SUM([Current Rolling Sales]),0.75)",
        datatype="real",
        role="measure",
        field_type="quantitative",
        table_calc="Columns",
    )
    editor.add_calculated_field(
        "Colour",
        COLOUR,
        datatype="string",
        role="dimension",
        field_type="nominal",
        table_calc="Columns",
    )
    editor.add_calculated_field(
        "Sales Contraction Indicator",
        "IF [Difference]<0 THEN '\u25cf' ELSE '' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Sub-Category (copy)",
        "[Sub-Category]",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Month Order Date",
        "MONTH([Order Date])",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )

    # --- Chart --------------------------------------------------------------
    # Three panes: the labelled current-sales bars, the same bars coloured by
    # the quartile, and the previous-sales Gantt bar behind them.
    tooltip = [
        "Sub-Category",
        "SUM(Current Rolling Sales)",
        "SUM(Previous Rolling Sales)",
        "SUM(Difference)",
    ]
    tooltip_runs = [
        {"field": "Sub-Category", "bold": True},
        {"text": "\n"},
        {"field": "SUM(Current Rolling Sales)", "fontsize": 9},
        {"text": " Current Rolling Sales", "fontsize": 9},
        {"text": "\n"},
        {"field": "SUM(Previous Rolling Sales)", "fontsize": 9},
        {"text": " Previous Rolling Sales", "fontsize": 9},
        {"text": "\n"},
        {"text": "------------------------------------------", "fontsize": 9},
        {"text": "\n"},
        {"field": "SUM(Difference)", "fontsize": 9},
        {"text": " Difference between the Current and Previous Rolling Period", "fontsize": 9},
    ]
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["Current Rolling Sales", "Previous Rolling Sales"],
        rows=["Sub-Category", "Sales Contraction Indicator", "Sub-Category (copy)"],
        axis_shelf="columns",
        fold_axes=True,
        synchronized=True,
        sort_field="Sub-Category (copy)",
        sort_descending="SUM(Current Rolling Sales)",
        sort_mode="computed",
        panes=[
            {
                "axis": "Current Rolling Sales",
                "mark_type": "Bar",
                "color": "Colour",
                "color_map": QUARTILE_COLORS,
                "label": "Label:Current Rolling Sales",
                "detail_extra": ["Sub-Category"],
                "tooltip": [],
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "has-stroke": "true",
                    "stroke-color": "#898989",
                },
            },
            {
                "axis": "Previous Rolling Sales",
                "mark_type": "GanttBar",
                "tooltip": [],
                "mark_style": {"mark-color": "#666666"},
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
        pane_datalabel_style={"font-size": "9", "color": "#000000"},
        cell_formats=[
            {"field": "Sales Contraction Indicator", "color": CIRCLE_RED},
            {"field": "Sub-Category", "height": 25},
            {"field": "Sub-Category (copy)", "height": 28},
        ],
        axis_style={
            "per_field": [
                {
                    "field": "Current Rolling Sales",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Current Rolling Sales",
                },
                {
                    "field": "Previous Rolling Sales",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Previous Rolling Sales",
                },
            ]
        },
    )
    for pane_index in (0, 1):
        editor.configure_custom_tooltip("Chart", tooltip_runs, pane_index=pane_index)

    # --- Month selector -----------------------------------------------------
    editor.add_worksheet("Month Selector")
    editor.configure_chart(
        "Month Selector",
        mark_type="Square",
        columns=["Month Order Date"],
        label="Month Order Date",
        tooltip=[],
        mark_sizing_off=True,
    )
    editor.configure_worksheet_style(
        "Month Selector",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"font-size": "8"},
        pane_mark_style={"mark-color": "#e6e6e6"},
    )
    editor.set_worksheet_rich_title("Month Selector", [{"text": "Select the # of Rolling Months", "fontsize": 9}])

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 800 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021 | WEEK 27  |  Top & Bottom Performers",
                    "font_size": 14,
                    "bold": True,
                }
            ],
            "absolute": pos(8, 8, 645, 60),
        },
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 72, 984, 646),
        },
        {
            "type": "worksheet",
            "name": "Month Selector",
            "show_title": True,
            "fit": "entire",
            "absolute": pos(653, 8, 339, 60),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Chart", "Month Selector"],
    )

    # Selecting a month square sets pRollingMonth, clearing resets it to 12.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Month Selector",
        source_field="Month Order Date",
        target_parameter="pRollingMonth",
        aggregation="sum",
        clear_behavior="set-value",
        clear_value="i:12",
        caption="Parameter1",
    )

    for name in ("Chart", "Month Selector"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
