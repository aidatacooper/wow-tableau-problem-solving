"""Build WW36's hover-driven custom axis and tracking reference lines."""

from pathlib import Path



HERE = Path(__file__).resolve().parent


from cwtwb.twb_editor import TWBEditor  # noqa: E402


HYPER = HERE / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUTS = HERE / "outputs"


def build(path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")


    # The set starts empty.  The dashboard hover action fills it with the
    # Custom Axis mark under the pointer and empties it on mouse leave.
    editor.add_calculated_field(
        "Month Order Date", "DATE(DATETRUNC('month', [Order Date]))",
        datatype="date", role="dimension", field_type="quantitative",
        default_format="*m-yyyy",
    )
    editor.add_set("Selected Date Set", "Month Order Date")
    editor.add_calculated_field(
        "Selected Date", "IF [Selected Date Set] THEN [Month Order Date] END",
        datatype="date", role="dimension", field_type="quantitative",
    )
    editor.add_calculated_field(
        "Max Date Month", "DATE(DATETRUNC('month', { FIXED : MAX([Order Date]) }))",
        datatype="date", role="dimension", field_type="quantitative",
    )
    editor.add_calculated_field(
        "Order Date Display", "IF [Month Order Date] = DATETRUNC('quarter', [Month Order Date]) "
        "OR [Month Order Date] = [Max Date Month] THEN [Month Order Date] END",
        datatype="date", role="dimension", field_type="quantitative",
        default_format="*m-yyyy",
    )
    editor.add_calculated_field(
        "Max Sales in Window", "WINDOW_MAX(SUM([Sales]))", datatype="real",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Sales Ref", "IF [Month Order Date] = [Selected Date] THEN [Sales] END",
        datatype="real",
    )
    editor.add_calculated_field(
        "Colour:Circle", "IF ISNULL([Order Date Display]) THEN 'teal' ELSE 'white' END",
        datatype="string", role="dimension", field_type="nominal",
    )

    editor.add_worksheet("Line Chart")
    editor.configure_chart(
        "Line Chart", mark_type="Line", columns=["[Month Order Date]"],
        rows=["SUM(Sales)"], tooltip=["SUM(Sales)"],
    )
    # Maximum Sales is always visible.  The next two lines are null while the
    # set is empty, then intersect at the hovered month and Sales value.
    editor.add_reference_line(
        "Line Chart", axis_field="SUM(Sales)", value_field="AGG(Max Sales in Window)",
        scope="per-pane", formula="max", label_type="custom",
        label="$<Value> in Sales", probability=None,
    )
    editor.add_reference_line(
        "Line Chart", axis_field="[Month Order Date]", value_field="ATTR(Selected Date)",
        scope="per-pane", formula="min", label_type="none", probability=None,
    )
    editor.add_reference_line(
        "Line Chart", axis_field="SUM(Sales)", value_field="SUM(Sales Ref)",
        scope="per-pane", formula="average", label_type="value",
    )
    editor.set_worksheet_selection_relaxation("Line Chart", enabled=True)
    editor.configure_custom_tooltip(
        "Line Chart",
        [
            {"field": "[Month Order Date]", "bold": True, "fontsize": 9},
            {"text": "\n"},
            {"text": "Sales:\t", "fontcolor": "#666666", "fontsize": 9},
            {"field": "SUM(Sales)", "bold": True, "fontcolor": "#666666", "fontsize": 9},
        ],
    )
    editor.configure_worksheet_style(
        "Line Chart", hide_gridlines=True, hide_zeroline=True,
        label_formats=[{"field": "SUM(Sales)", "font_size": "8", "text-format": 'c"$"#,##0;-"$"#,##0'}],
        axis_style={
            "stroke-size": "0", "line-visibility": "off",
            "tick-color": "#00000000",
            "encodings": [{"field": "SUM(Sales)", "class": "0", "scope": "rows", "range_type": "fixed", "min": 0, "max": 125000, "major_spacing": 20000, "major_origin": 0, "minor_show": False}],
            "per_field": [
                {"field": "[Month Order Date]", "attr": "display", "value": "false", "class": "0", "scope": "cols"},
                {"field": "SUM(Sales)", "attr": "title", "value": "", "class": "0", "scope": "rows"},
                {"field": "SUM(Sales)", "attr": "width", "value": "68"},
            ],
        },
        pane_mark_style={"mark-color": "#499894", "mark-markers-mode": "all"},
    )
    editor.configure_reference_line_style(
        "Line Chart", "refline0", {
            "fill-above": "#00000000", "fill-below": "#00000000",
            "line-visibility": "on", "line-pattern-only": "dotted",
            "stroke-color": "#499894", "vertical-align": "bottom",
            "font-family": "Tableau Medium", "color": "#499894",
            "font-weight": "bold", "font-size": "9",
        },
    )
    editor.configure_reference_line_style(
        "Line Chart", "refline1", {
            "fill-above": "#00000000", "fill-below": "#00000000",
            "line-visibility": "on", "line-pattern-only": "dotted",
            "stroke-color": "#499894", "stroke-size": "2",
        },
    )
    editor.configure_reference_line_style(
        "Line Chart", "refline2", {
            "fill-above": "#00000000", "fill-below": "#00000000",
            "line-visibility": "on", "line-pattern-only": "dotted",
            "stroke-color": "#499894", "vertical-align": "bottom",
            "font-family": "Tableau Medium", "color": "#499894",
            "font-weight": "bold",
        },
    )

    editor.add_worksheet("Custom Axis")
    editor.configure_chart(
        "Custom Axis", mark_type="Circle", columns=["[Month Order Date]"],
        color="Colour:Circle", label="[Order Date Display]", tooltip=["SUM(Sales)"],
        color_map={"teal": "#499894", "white": "#ffffff"}, mark_sizing_off=True,
    )
    editor.set_worksheet_selection_relaxation("Custom Axis", enabled=True)
    editor.configure_custom_tooltip(
        "Custom Axis",
        [
            {"field": "[Month Order Date]", "bold": True, "fontsize": 9},
            {"text": "\n"},
            {"text": "Sales:\t", "fontcolor": "#666666", "fontsize": 9},
            {"field": "SUM(Sales)", "bold": True, "fontcolor": "#666666", "fontsize": 9},
        ],
    )
    editor.configure_worksheet_style(
        "Custom Axis", hide_axes=True, hide_gridlines=True, hide_zeroline=True,
        hide_borders=True, hide_table_dividers=True,
        cell_formats=[{"height": "60"}],
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={
            "color-mode": "user", "color": "#898989",
            "font-weight": "normal", "font-size": "8",
        },
        pane_mark_style={
            "mark-color": "#499894", "mark-markers-mode": "all",
            "mark-labels-show": "true", "size": "0.31784531474113464",
            "mark-labels-cull": "false",
        },
    )
    editor.add_worksheet("Data")
    editor.configure_chart("Data", mark_type="Text", columns=["[Month Order Date]"], rows=["SUM(Sales)"])

    dashboard_name = "WW36 Custom Axis Tracker"
    editor.add_dashboard(
        dashboard_name, width=1000, height=800,
        layout={"type": "container", "direction": "vertical", "children": [
            {"type": "text", "text": "Can you build a custom axis with a tracking reference line?", "runs": [{"text": "Can you build a custom axis with a tracking reference line?", "font_size": "15", "font_alignment": "0", "font_color": "#898989"}], "fixed_size": 45},
            {"type": "worksheet", "name": "Custom Axis", "fit": "width", "fixed_size": 65, "show_title": False},
            {"type": "worksheet", "name": "Line Chart", "fit": "entire", "weight": 1, "show_title": False},
            {"type": "text", "text": "DESIGNED BY: Curtis Harris                  #WORKOUTWEDNESDAY | 2019 | WEEK 36                 RECREATED BY: Donna Coles", "font_size": "8", "font_color": "#499894", "fixed_size": 60},
            {"type": "text", "runs": [{"text": "http://www.workout-wednesday.com/week-36-can-you-build-a-custom-axis-with-a-tracking-reference-line/", "font_size": "8", "font_color": "#006b9e", "hyperlink": "http://www.workout-wednesday.com/week-36-can-you-build-a-custom-axis-with-a-tracking-reference-line/"}], "fixed_size": 25},
            {"type": "empty", "fixed_size": 135},
        ]}, worksheet_names=["Line Chart", "Custom Axis"],
    )
    editor.add_dashboard_set_action(
        dashboard_name, "Custom Axis", "Selected Date Set", event_type="on-hover",
        caption="Select Date", clear_option="exclude-all",
    )
    OUTPUTS.mkdir(exist_ok=True)
    editor.save(path)
    return path


if __name__ == "__main__":
    for name in (
        "2019-09-09-ww36-custom-axis-tracker-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUTS / name))
