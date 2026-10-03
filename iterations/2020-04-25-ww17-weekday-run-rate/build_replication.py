"""Build a compact regional weekday run-rate dashboard with native blending."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_04_22_WW17_Weekday_RunRate"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/TEMP_0w4rjxf1y3op0w154ltbd1f67pji.hyper"))
    primary = e.select_datasource("Sample _ Superstore (Simple)")
    secondary = e.add_hyper_datasource(
        "Plan", str(HERE / "inputs/TEMP_0jid4k908s0rnf1fdypy20ecq2fb.hyper")
    )
    e.add_calculated_field(
        "BLEND:Date", "[Date]", datatype="date", role="dimension", field_type="ordinal"
    )
    e.select_datasource(primary)
    e.add_calculated_field(
        "BLEND:Date",
        "DATE(DATETRUNC('month',[Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.import_blended_field("Plan", secondary, "SUM(Plan)")
    specs = [
        ("Today", "{FIXED:MAX([Date])}", "date", "dimension", "ordinal"),
        (
            "Start of Month",
            "DATE(DATETRUNC('month',[Today]))",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "End of Month",
            "DATE(DATEADD('day',-1,DATEADD('month',1,[Start of Month])))",
            "date",
            "dimension",
            "ordinal",
        ),
        (
            "Current Month",
            "[Date]>=[Start of Month] AND [Date]<=[Today]",
            "boolean",
            "dimension",
            "nominal",
        ),
        (
            "Weekdays Elapsed",
            "DATEDIFF('day',[Start of Month],[Today])+1-2*DATEDIFF('week',[Start of Month],[Today],'sunday')-IF DATEPART('weekday',[Start of Month],'sunday')=1 THEN 1 ELSE 0 END-IF DATEPART('weekday',[Today],'sunday')=7 THEN 1 ELSE 0 END",
            "integer",
            "dimension",
            "ordinal",
        ),
        (
            "Weekdays in Month",
            "DATEDIFF('day',[Start of Month],[End of Month])+1-2*DATEDIFF('week',[Start of Month],[End of Month],'sunday')-IF DATEPART('weekday',[Start of Month],'sunday')=1 THEN 1 ELSE 0 END-IF DATEPART('weekday',[End of Month],'sunday')=7 THEN 1 ELSE 0 END",
            "integer",
            "dimension",
            "ordinal",
        ),
        ("MTD Sales", "SUM([Sales])", "real", "measure", "quantitative"),
        (
            "Run Rate",
            "[MTD Sales]/MIN([Weekdays Elapsed])*MIN([Weekdays in Month])",
            "real",
            "measure",
            "quantitative",
        ),
        ("Under Plan", "[Run Rate]<[Plan]", "boolean", "dimension", "nominal"),
        (
            "Run Rate Red",
            "IF [Under Plan] THEN [Run Rate] END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Run Rate Gray",
            "IF NOT [Under Plan] THEN [Run Rate] END",
            "real",
            "measure",
            "quantitative",
        ),
        ("Zero", "0", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, field_type in specs:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=field_type
        )
        if role == "measure" and name != "Zero":
            e.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Plan", 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Today", "*dd mmm yyyy")
    metrics = ["MTD Sales", "Run Rate", "Plan"]
    filters = [{"column": "Current Month", "values": [True]}]
    links = {"Region": "Region", "BLEND:Date": "BLEND:Date"}
    e.add_worksheet("Data")
    e.configure_chart(
        "Data",
        mark_type="Text",
        rows=["Region"],
        label="MTD Sales",
        tooltip=metrics,
        filters=filters,
    )
    e.configure_datasource_blend("Data", secondary, links, ["SUM(Plan)"])
    e.add_worksheet("Title")
    e.configure_chart(
        "Title",
        mark_type="Text",
        rows=["MIN(Zero)"],
        label="ATTR(Today)",
        label_runs=[
            {
                "text": "Monthly Sales Projection\n",
                "fontsize": "20",
                "fontcolor": "#606b76",
                "fontalignment": "0",
                "fontname": "Tableau Medium",
            },
            {"text": "Data until ", "fontsize": "12", "fontcolor": "#606b76"},
            {"field": "ATTR(Today)", "fontsize": "12", "fontcolor": "#606b76"},
        ],
    )
    e.configure_worksheet_style(
        "Title",
        background_color="#f5f5f5",
        disable_tooltip=True,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        pane_mark_style={"mark-labels-show": "true"},
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
    )
    e.set_worksheet_title("Title", "")
    e.add_worksheet("Viz")
    runs = [
        {"field": "Region", "bold": True, "fontsize": "12", "fontcolor": "#606b76"},
        {"text": "\nMTD ", "fontsize": "10", "fontcolor": "#606b76"},
        {"field": "MTD Sales", "fontsize": "12", "fontcolor": "#606b76"},
        {"text": "\nRun Rate ", "fontsize": "10", "fontcolor": "#606b76"},
        {"field": "Run Rate Red", "fontsize": "12", "fontcolor": "#e03426"},
        {"field": "Run Rate Gray", "fontsize": "12", "fontcolor": "#606b76"},
        {"text": "\nPlan ", "fontsize": "10", "fontcolor": "#606b76"},
        {"field": "Plan", "fontsize": "12", "fontcolor": "#000000"},
    ]
    for run in runs:
        run["fontalignment"] = "0"
        run["fontname"] = "Tableau Medium"
    e.configure_layered_chart(
        "Viz",
        rows=["Region"],
        columns=["MIN(Zero)", "Run Rate", "Plan"],
        panes=[
            {
                "axis": "MIN(Zero)",
                "mark_type": "Text",
                "label_runs": runs,
                "labels": [
                    "Region",
                    "MTD Sales",
                    "Plan",
                    "Run Rate Red",
                    "Run Rate Gray",
                ],
            },
            {
                "axis": "Run Rate",
                "mark_type": "Bar",
                "color": "Under Plan",
                "mark_style": {
                    "size": "0.7356353402",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
                "mark_sizing_off": True,
                "tooltip": metrics,
            },
            {
                "axis": "Plan",
                "mark_type": "GanttBar",
                "mark_style": {
                    "size": "1.5052486658",
                    "mark-color": "#000000",
                    "has-stroke": "true",
                    "stroke-color": "#000000",
                },
                "mark_sizing_off": True,
                "tooltip": metrics,
            },
        ],
        axis_shelf="cols",
        fold_axes=False,
        hide_axes=True,
        filters=filters,
    )
    e.configure_datasource_blend("Viz", secondary, links, ["SUM(Plan)"])
    e.set_datasource_color_palette(
        "Under Plan", {"true": "#e03426", "false": "#606b76"}
    )
    e.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=False,
        table_dividers=[
            {
                "scope": "rows",
                "stroke-size": "1",
                "stroke-color": "#e6e6e6",
                "line-visibility": "on",
                "div-level": "1",
            },
            {"scope": "cols", "stroke-size": "0", "line-visibility": "off"},
        ],
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_sort_controls=True,
        axis_style={
            "encodings": [
                {
                    "field": "Plan",
                    "attr": "space",
                    "type": "space",
                    "scope": "cols",
                    "field-type": "quantitative",
                    "fold": True,
                    "synchronized": True,
                }
            ]
        },
        cell_formats=[{"height": "114"}],
        disable_tooltip=True,
        hide_row_label="Region",
        panes_style={
            "1": {
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
                "cell_style": {"text-align": "left", "vertical-align": "center"},
            },
            "2": {"cell_style": {"text-align": "left", "vertical-align": "bottom"}},
            "3": {
                "mark_style": {
                    "mark-color": "#000000",
                    "has-stroke": "true",
                    "stroke-color": "#000000",
                }
            },
        },
    )
    e.set_worksheet_title("Viz", "")

    def zone(name, x, y, w, h):
        return {
            "type": "worksheet",
            "name": name,
            "fit": "entire",
            "show_title": False,
            "absolute": {
                "x": round(x / 375 * 100000),
                "y": round(y / 667 * 100000),
                "w": round(w / 375 * 100000),
                "h": round(h / 667 * 100000),
            },
        }

    e.add_dashboard(
        DASHBOARD,
        width=375,
        height=667,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [zone("Title", 8, 8, 359, 118), zone("Viz", 8, 126, 359, 533)],
        },
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
