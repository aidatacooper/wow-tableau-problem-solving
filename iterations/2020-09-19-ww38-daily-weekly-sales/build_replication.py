"""Daily scaffold marks and independent weekly cumulative-sales Gantt bars."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_09_16_WW38_Daily_Weekly_Sales"
EVENT = "Event Description (DimEvent)"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_parameter(
        "Comparison",
        datatype="string",
        default_value="Event Year",
        domain_type="list",
        allowed_values=["Event Year", "YoY Event"],
    )
    editor.add_parameter(
        "Event Group",
        datatype="integer",
        default_value="0",
        alias="All",
        domain_type="list",
        allowed_values=["0", "1", "2"],
        allowed_aliases={"0": "All", "1": "Spring Event", "2": "Fall Event"},
    )
    dimensions = {
        "Week No From Launch": (
            "DATEDIFF('week',DATE(DATETRUNC('week',[Launch Date],'Monday')),DATE(DATETRUNC('week',[Actual Date],'Monday')))+1",
            "integer",
            "ordinal",
        ),
        "Day Position": (
            "IF [Day of Week]=1 THEN 7 ELSE [Day of Week]-1 END",
            "integer",
            "quantitative",
        ),
        "Type of Day": (
            "IF [Actual Date]=[Launch Date] THEN 'Launch Date' ELSEIF [Actual Date]=[Event Date (Dim Event)] THEN 'Event Date' ELSE 'Regular' END",
            "string",
            "nominal",
        ),
        "Display": (
            "IF [Comparison]='Event Year' THEN LEFT([Event Description (DimEvent)],4) ELSE RIGHT([Event Description (DimEvent)],2) END",
            "string",
            "nominal",
        ),
        "Event Group Filter": (
            "([Event Group]=1 AND DATEPART('quarter',[Event Date (Dim Event)])<=2) OR ([Event Group]=2 AND DATEPART('quarter',[Event Date (Dim Event)])>2) OR [Event Group]=0",
            "boolean",
            "nominal",
        ),
    }
    for name, (formula, datatype, field_type) in dimensions.items():
        editor.add_calculated_field(
            name, formula, datatype=datatype, role="dimension", field_type=field_type
        )
    editor.add_calculated_field("Ticket Sales", "ZN([Sold Amount])", datatype="integer")
    editor.add_calculated_field("Zero", "MIN(0)", datatype="integer")
    editor.add_calculated_field("One", "1", datatype="integer")
    for name, formula in {
        "Total Sales Per Event": "TOTAL(SUM([Sold Amount]))",
        "Cumulative Sales": "RUNNING_SUM(SUM([Ticket Sales]))",
        "% Total Sales": "RUNNING_SUM(SUM([Ticket Sales]))/[Total Sales Per Event]",
    }.items():
        editor.add_calculated_field(name, formula, table_calc="Rows")
    for name in ["Ticket Sales", "Total Sales Per Event", "Cumulative Sales"]:
        editor.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("% Total Sales", "p0.0%")
    address = {"ordering_type": "Field", "ordering_field": "Week No From Launch"}
    overrides = {
        "Total Sales Per Event": [address],
        "Cumulative Sales": [address],
        "% Total Sales": [address, {"field": "Total Sales Per Event", **address}],
    }
    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        columns=["Week No From Launch", "Zero", "[Day Position]"],
        rows=["Display", EVENT],
        axis_shelf="cols",
        synchronized=False,
        fold_axes=False,
        hide_axes=True,
        filters=[{"column": "Event Group Filter", "values": [True]}],
        table_calc_overrides=overrides,
        panes=[
            {
                "axis": "[Day Position]",
                "mark_type": "GanttBar",
                "color": "Type of Day",
                "mark_sizing_off": True,
                "color_map": {
                    "Launch Date": "#636059",
                    "Event Date": "#636059",
                    "Regular": "#ffffff",
                },
                "tooltip": [
                    "SUM(Ticket Sales)",
                    "ATTR(Actual Date)",
                    "ATTR(Day of Week Abbrev)",
                ],
                "mark_style": {
                    "size": "1.637182354927063",
                    "has-stroke": "true",
                    "stroke-color": "#d4d4d4",
                },
            },
            {
                "axis": "Zero",
                "mark_type": "GanttBar",
                "size": "MIN(One)",
                "color": "% Total Sales",
                "mark_sizing_off": True,
                "tooltip": [
                    "Cumulative Sales",
                    "SUM(Ticket Sales)",
                    "% Total Sales",
                    "Total Sales Per Event",
                ],
                "mark_style": {
                    "size": "1.0434806346893311",
                    "has-stroke": "true",
                    "stroke-color": "#333333",
                    "mark-selectionrelaxation": "mark-selectionrelaxation-disallow",
                },
            },
        ],
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        cell_formats=[{"field": EVENT, "height": "88"}],
        label_formats=[
            {"field": "Display", "display": "false"},
            {"field": "Week No From Launch", "display": "false"},
            {
                "field": EVENT,
                "font-weight": "bold",
                "color": "#333333",
                "text-align": "center",
            },
        ],
        axis_style={
            "render-fold-reversed": "true",
            "encodings": [
                {
                    "field": "[Day Position]",
                    "attr": "space",
                    "type": "space",
                    "scope": "cols",
                    "field-type": "quantitative",
                    "fold": "true",
                },
                {
                    "field": "Zero",
                    "attr": "space",
                    "type": "space",
                    "scope": "cols",
                    "field-type": "quantitative",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                },
            ],
        },
        color_style={
            "field": "% Total Sales",
            "colors": ["#f1f1f1", "#7a996d"],
            "num_steps": 4,
        },
    )
    for sheet, rows, measures, filters in [
        (
            "CHK:Daily Data",
            [EVENT, "[Actual Date]"],
            ["SUM(Ticket Sales)"],
            [
                {
                    "column": EVENT,
                    "values": ["2019 EVENT #1", "2020 EVENT #1", "2020 EVENT #6"],
                }
            ],
        ),
        (
            "CHK:Weekly Data",
            [EVENT, "Week No From Launch"],
            [
                "SUM(Ticket Sales)",
                "Cumulative Sales",
                "Total Sales Per Event",
                "% Total Sales",
            ],
            [{"column": EVENT, "values": ["2020 EVENT #6"]}],
        ),
    ]:
        editor.add_worksheet(sheet)
        editor.configure_layered_chart(
            sheet,
            rows=rows,
            columns=["Measure Names"],
            panes=[
                {
                    "mark_type": "Text",
                    "label": "Multiple Values",
                    "measure_values": measures,
                }
            ],
            filters=filters,
            table_calc_overrides=overrides if "Weekly" in sheet else None,
        )
    editor.add_dashboard(
        DASHBOARD,
        width=1600,
        height=900,
        worksheet_names=["Viz"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "horizontal",
                    "fixed_size": 78,
                    "children": [
                        {
                            "type": "vertical",
                            "fixed_size": 1100,
                            "children": [
                                {
                                    "type": "text",
                                    "text": "Can you visualise daily and weekly ticket sales in the same view?",
                                    "font_size": 15,
                                    "font_color": "#333333",
                                    "bold": True,
                                },
                                {
                                    "type": "color",
                                    "worksheet": "Viz",
                                    "field": "Type of Day",
                                    "pane_index": 1,
                                    "show_title": False,
                                    "fixed_size": 28,
                                },
                            ],
                        },
                        {
                            "type": "color",
                            "worksheet": "Viz",
                            "field": "% Total Sales",
                            "pane_index": 2,
                            "fixed_size": 200,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "Event Group",
                            "mode": "compact",
                            "fixed_size": 150,
                        },
                        {
                            "type": "paramctrl",
                            "parameter": "Comparison",
                            "mode": "list",
                            "fixed_size": 150,
                        },
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": False,
                    "fit": "entire",
                },
                {
                    "type": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "text": "DESIGNED BY : JAMIE DELAGRANGE",
                            "font_size": 8,
                            "font_color": "#7a996d",
                            "bold": True,
                        },
                        {
                            "type": "text",
                            "text": "#WOW2020 | WEEK 38",
                            "font_size": 8,
                            "font_color": "#7a996d",
                            "bold": True,
                        },
                        {
                            "type": "text",
                            "text": "RECREATED WITH CWTWB | DONNA COLES REFERENCE",
                            "font_size": 8,
                            "font_color": "#7a996d",
                            "bold": True,
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "https://www.workout-wednesday.com/2020w38/",
                    "font_size": 8,
                    "font_color": "#7a996d",
                    "fixed_size": 32,
                },
            ],
        },
    )
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
