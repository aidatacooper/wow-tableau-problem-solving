"""Native set-driven Sunday-week to day drilldown and reset parameter actions."""

from pathlib import Path
from datetime import datetime
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_05_06_WW19_DateDrillDown"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/TEMP_09kc2h61hrhcdy1c4xpse05a8k3z.hyper")
    )
    editor.set_date_options(start_of_week="sunday")
    editor.add_parameter("Drill Down", "integer", "0", domain_type="any")
    editor.add_calculated_field(
        "Date to Plot",
        "IF [Drill Down]>0 THEN DATETRUNC('day',[Order Date]) ELSE DATETRUNC('week',[Order Date],'sunday') END",
        datatype="datetime",
        role="dimension",
        field_type="quantitative",
    )
    editor.add_set(
        "Selected Dates",
        "Date to Plot",
        members=[datetime(2019, 11, 2), datetime(2019, 11, 3), datetime(2019, 11, 6)],
    )
    calculations = [
        (
            "Min Date",
            "{FIXED:MIN(IF [Selected Dates] OR [Drill Down]=0 THEN DATETRUNC('week',[Date to Plot],'sunday') END)}",
            "datetime",
            "dimension",
            "quantitative",
        ),
        (
            "Max Date",
            "IF [Drill Down]=0 THEN {FIXED:MAX(DATEADD('day',-1,[Date to Plot]))} ELSE DATEADD('week',1,{FIXED:MAX(IF [Selected Dates] THEN DATETRUNC('week',[Date to Plot],'sunday') END)})-1 END",
            "datetime",
            "dimension",
            "quantitative",
        ),
        (
            "Dates To Include",
            "[Order Date]>=[Min Date] AND [Order Date]<=[Max Date]",
            "boolean",
            "dimension",
            "nominal",
        ),
        ("Set Drill Down Level", "1", "integer", "dimension", "ordinal"),
        ("Reset", "0", "integer", "dimension", "ordinal"),
        ("Show Reset", "[Drill Down]=1", "boolean", "dimension", "nominal"),
        ("COLOUR", "[Drill Down]", "integer", "dimension", "ordinal"),
        (
            "LABEL:Level",
            "IF [Drill Down]>0 THEN 'Day' ELSE 'Week' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "LABEL:Instruction",
            "IF [Drill Down]=0 THEN 'SELECT WEEKS TO DRILL DOWN TO DAILY VIEW' ELSE 'CLEAR SELECTION USING BUTTON' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Heading",
            "IF [Drill Down]>0 THEN 'DAILY SALES' ELSE 'WEEKLY SALES' END",
            "string",
            "dimension",
            "nominal",
        ),
        ("Button", "'CLEAR SELECTION'", "string", "dimension", "nominal"),
        ("One", "1", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, kind in calculations:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    for name, formula in [
        ("Total Sales", "WINDOW_SUM(SUM([Sales]))"),
        ("Avg Sales", "WINDOW_AVG(SUM([Sales]))"),
    ]:
        editor.add_calculated_field(name, formula, table_calc="Rows")
    editor.set_field_format("Sales", 'c"$"#,##0;-"$"#,##0')
    for name in ["Total Sales", "Avg Sales"]:
        editor.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    editor.add_worksheet("Chart")
    address = {"ordering_type": "Field", "ordering_field": "[Date to Plot]"}
    editor.configure_layered_chart(
        "Chart",
        columns=["[Date to Plot]"],
        rows=["SUM(Sales)"],
        panes=[
            {
                "axis": "SUM(Sales)",
                "mark_type": "Line",
                "color": "COLOUR",
                "color_map": {"0": "#d4d4d4", "1": "#a26dc2"},
                "detail": "Set Drill Down Level",
                "tooltip": ["Dates To Include"],
                "detail_extra": [
                    "LABEL:Level",
                    "Min Date",
                    "Max Date",
                    "Total Sales",
                    "Avg Sales",
                    "LABEL:Instruction",
                    "Heading",
                ],
            }
        ],
        filters=[{"column": "Dates To Include", "values": [True]}],
        table_calc_overrides={"Total Sales": [address], "Avg Sales": [address]},
    )
    editor.add_reference_line(
        "Chart",
        axis_field="SUM(Sales)",
        value_field="SUM(Sales)",
        scope="per-table",
        formula="average",
        tooltip="Average = <Value>",
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        axis_style={"font-size": "9", "title": ""},
        pane_mark_style={"size": "0.35"},
        pane_cell_style={"font-size": "9"},
    )
    editor.add_calculated_field(
        "Complete Title",
        "'Superstore Sales by '+MIN([LABEL:Level])+' ('+STR(DATE(MIN([Min Date])))+' to '+STR(DATE(MIN([Max Date])))+')'+CHAR(10)+MIN([LABEL:Instruction])+CHAR(10)+'Total Sales in View: $'+STR(ROUND(SUM([Sales]),0))+' | Average '+MIN([LABEL:Level])+' Sales: $'+STR(ROUND(SUM([Sales])/COUNTD([Date to Plot]),0))",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.add_worksheet("Title")
    editor.configure_layered_chart(
        "Title",
        columns=[],
        rows=[],
        panes=[
            {
                "mark_type": "Text",
                "label": "Complete Title",
                "label_runs": [
                    {
                        "field": "Complete Title",
                        "fontsize": 11,
                        "fontname": "Tableau Medium",
                    }
                ],
            }
        ],
        filters=[{"column": "Dates To Include", "values": [True]}],
    )
    editor.configure_worksheet_style(
        "Title",
        hide_axes=True,
        hide_borders=True,
        hide_gridlines=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
        table_formats=[
            {"attr": "cell-width", "value": "1000"},
            {"attr": "cell-height", "value": "90"},
        ],
    )
    editor.add_worksheet("Reset")
    editor.configure_layered_chart(
        "Reset",
        columns=["MIN(One)"],
        rows=[],
        axis_shelf="columns",
        panes=[
            {
                "axis": "MIN(One)",
                "mark_type": "Bar",
                "label": "Button",
                "detail": "Reset",
                "tooltip": ["Show Reset"],
                "label_runs": [
                    {
                        "field": "Button",
                        "fontsize": 9,
                        "fontcolor": "#ffffff",
                        "bold": True,
                    }
                ],
            }
        ],
        filters=[{"column": "Show Reset", "values": [True]}],
        hide_axes=True,
    )
    editor.configure_worksheet_style(
        "Reset",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        disable_tooltip=True,
        pane_mark_style={
            "mark-color": "#a26dc2",
            "size": "1",
            "mark-labels-show": "true",
        },
        pane_cell_style={"text-align": "center", "font-size": "9"},
        axis_style={"min": "0", "max": "1"},
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=700,
        worksheet_names=["Title", "Chart", "Reset"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "worksheet",
                    "name": "Title",
                    "show_title": False,
                    "fit": "entire",
                    "fixed_size": 90,
                },
                {"type": "worksheet", "name": "Chart", "show_title": False},
                {
                    "type": "horizontal",
                    "fixed_size": 45,
                    "children": [
                        {"type": "empty"},
                        {
                            "type": "worksheet",
                            "name": "Reset",
                            "show_title": False,
                            "fit": "entire",
                        },
                        {"type": "empty"},
                    ],
                },
                {
                    "type": "text",
                    "fixed_size": 45,
                    "font_size": 8,
                    "text": "DESIGNED BY: ANN JACKSON | #WOW2020 WEEK 19 | RECREATED WITH CWTWB\nhttps://www.workout-wednesday.com/2020w19/",
                },
            ],
        },
    )
    editor.add_dashboard_set_action(
        DASHBOARD,
        "Chart",
        "Selected Dates",
        event_type="on-select",
        caption="Drill Down",
        clear_option="do-nothing",
        selection_mode="assign",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Chart",
        source_field="Set Drill Down Level",
        target_parameter="Drill Down",
        caption="Set Drill Down",
        clear_behavior="keep-current",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Reset",
        source_field="Reset",
        target_parameter="Drill Down",
        caption="Reset",
        clear_behavior="keep-current",
    )
    editor.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(path, validate=False)
    return path


if __name__ == "__main__":
    print(build())
