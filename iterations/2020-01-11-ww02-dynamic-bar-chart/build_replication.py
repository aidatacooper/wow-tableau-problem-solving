"""Independent dynamic metric/date bar chart using extracted Superstore data."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_01_08_WW01_Beautiful_Dynamic_Bar_Chart"
MEASURES = [" Sales ", " Profit Ratio ", " Items Per Order "]
PERIODS = ["Last 12 Months", "Last 13 Weeks", "Last 14 Days"]
COLORS = ["#9264a5", "#86b35e", "#63ccc6"]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    editor.set_date_options(start_of_week="sunday")
    editor.add_parameter("Today", "date", "#2020-01-01#", domain_type="any")
    editor.add_parameter(
        "Date Period", "string", PERIODS[0], domain_type="list", allowed_values=PERIODS
    )
    editor.add_parameter("Selected Measure", "string", MEASURES[0], domain_type="any")
    for name, formula, datatype, role, fmt in [
        ("Profit Ratio", "SUM([Profit])/SUM([Sales])", "real", "measure", "p0.0%"),
        (
            "Items Per Order",
            "SUM([Quantity])/COUNTD([Order ID])",
            "real",
            "measure",
            "n#,##0.0;-#,##0.0",
        ),
        (
            "Order Date Truncate",
            "DATE(CASE [Date Period] WHEN 'Last 12 Months' THEN DATETRUNC('month',[Order Date]) WHEN 'Last 13 Weeks' THEN DATETRUNC('week',[Order Date]) ELSE DATETRUNC('day',[Order Date]) END)",
            "date",
            "dimension",
            None,
        ),
        (
            "Dates to Include",
            "CASE [Date Period] WHEN 'Last 12 Months' THEN [Order Date] >= DATEADD('month',-12,[Today]) WHEN 'Last 13 Weeks' THEN [Order Date] >= DATEADD('week',-13,[Today]) ELSE [Order Date] >= DATEADD('day',-14,[Today]) END",
            "boolean",
            "dimension",
            None,
        ),
        (
            "Label:Date",
            "CASE [Date Period] WHEN 'Last 12 Months' THEN LEFT(DATENAME('month',[Order Date Truncate]),3) + \"'\" + RIGHT(STR(YEAR([Order Date Truncate])),2) WHEN 'Last 13 Weeks' THEN 'Week ' + STR(DATEPART('week',[Order Date Truncate])) ELSE STR(DATEPART('month',[Order Date Truncate])) + '/' + STR(DATEPART('day',[Order Date Truncate])) END",
            "string",
            "dimension",
            None,
        ),
        (
            "Measure to Show",
            "CASE [Selected Measure] WHEN ' Sales ' THEN SUM([Sales]) WHEN ' Profit Ratio ' THEN [Profit Ratio] WHEN ' Items Per Order ' THEN [Items Per Order] END",
            "real",
            "measure",
            None,
        ),
        ("Metric Color", "[Selected Measure]", "string", "dimension", None),
        (
            "Label:Sales",
            "IF [Selected Measure] = ' Sales ' THEN '$' + REGEXP_REPLACE(STR(INT(ROUND(SUM([Sales]),0))), '(\\d)(?=(\\d{3})+$)', '$1,') END",
            "string",
            "measure",
            None,
        ),
        (
            "Label:Profit Ratio",
            "IF [Selected Measure] = ' Profit Ratio ' THEN [Profit Ratio] END",
            "real",
            "measure",
            "p0.0%",
        ),
        (
            "Label:Items Per Order",
            "IF [Selected Measure] = ' Items Per Order ' THEN [Items Per Order] END",
            "real",
            "measure",
            "n#,##0.0;-#,##0.0",
        ),
        ("True", "TRUE", "boolean", "dimension", None),
        ("False", "FALSE", "boolean", "dimension", None),
    ]:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, default_format=fmt
        )
    editor.add_worksheet("Chart")
    editor.add_worksheet("Selector")
    editor.configure_chart(
        "Chart",
        mark_type="Bar",
        columns=["[Order Date Truncate]", "Label:Date"],
        rows=["Measure to Show"],
        color="Metric Color",
        color_map=dict(zip(MEASURES, COLORS)),
        label="Label:Sales",
        label_extra=["Label:Profit Ratio", "Label:Items Per Order"],
        label_runs=[
            {"field": "Label:Sales"},
            {"field": "Label:Profit Ratio"},
            {"field": "Label:Items Per Order"},
        ],
        filters=[{"column": "Dates to Include", "values": [True]}],
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_axes=True,
        hide_row_label="[Order Date Truncate]",
        hide_gridlines=True,
        hide_zeroline=False,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        pane_cell_style={"text-align": "center"},
        pane_datalabel_style={"font-size": "10", "font-family": "Tableau Book"},
        pane_mark_style={
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
            "size": "0.8",
        },
        label_formats=[{"field": "Label:Date", "font-size": "10"}],
        gridline_style={"rows": {"stroke-size": "0", "line-visibility": "off"}},
    )
    editor.configure_custom_tooltip(
        "Chart",
        [
            {"field": "Label:Date", "bold": True},
            {"text": "\n"},
            {"field": "Label:Sales"},
            {"field": "Label:Profit Ratio"},
            {"field": "Label:Items Per Order"},
        ],
    )
    panes = []
    for i, choice in enumerate(MEASURES):
        editor.add_calculated_field(choice, "MIN(0)", datatype="real")
        editor.add_calculated_field(
            f"Selector Label {i}",
            f"IF [Selected Measure] = '{choice}' THEN '● {choice.strip()}' ELSE '○ {choice.strip()}' END",
            datatype="string",
            role="dimension",
        )
        panes.append(
            {
                "axis": f"[{choice}]",
                "mark_type": "Text",
                "label": f"Selector Label {i}",
                "labels": ["Measure Names"],
                "detail_extra": ["True", "False"],
                "mark_style": {
                    "mark-color": COLORS[i],
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
                "label_runs": [{"field": f"Selector Label {i}"}],
            }
        )
    editor.configure_layered_chart(
        "Selector",
        columns=[f"[{choice}]" for choice in MEASURES],
        panes=panes,
        axis_shelf="columns",
        fold_axes=False,
    )
    editor.configure_worksheet_style(
        "Selector",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        panes_style={
            str(i + 1): {
                "datalabel_style": {
                    "font-size": "11",
                    "font-weight": "bold",
                    "color-mode": "user",
                    "color": color,
                }
            }
            for i, color in enumerate(COLORS)
        },
    )
    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "parameter": "Selected Measure",
                    "font_size": "12",
                    "font_color": "#333333",
                    "font_alignment": "0",
                },
                {
                    "text": " | ",
                    "font_size": "12",
                    "font_color": "#333333",
                    "font_alignment": "0",
                },
                {
                    "parameter": "Date Period",
                    "font_size": "12",
                    "font_color": "#333333",
                    "font_alignment": "0",
                },
            ],
            "absolute": {"x": 727, "y": 1000, "w": 34273, "h": 4705},
        },
        {
            "type": "worksheet",
            "name": "Selector",
            "show_title": False,
            "fit": "entire",
            "absolute": {"x": 35000, "y": 1000, "w": 51545, "h": 4705},
        },
        {
            "type": "paramctrl",
            "parameter": "Date Period",
            "mode": "compact",
            "show_title": False,
            "absolute": {"x": 86545, "y": 1000, "w": 12728, "h": 4705},
        },
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": False,
            "fit": "entire",
            "absolute": {"x": 727, "y": 9378, "w": 98546, "h": 81622},
        },
        {
            "type": "text",
            "text": "DESIGNED BY : ANN JACKSON          #WOW2020 | WEEK 2          RECREATED WITH CWTWB",
            "runs": [
                {
                    "text": "DESIGNED BY : ANN JACKSON          #WOW2020 | WEEK 2          RECREATED WITH CWTWB",
                    "font_size": "8",
                    "font_color": "#63ccc6",
                    "font_alignment": "1",
                }
            ],
            "absolute": {"x": 727, "y": 93000, "w": 98546, "h": 3500},
        },
        {
            "type": "text",
            "text": "https://www.workout-wednesday.com/2020w02/",
            "absolute": {"x": 727, "y": 97000, "w": 98546, "h": 2500},
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1100,
        height=800,
        worksheet_names=["Chart", "Selector"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Selector",
        source_field="Measure Names",
        target_parameter="Selected Measure",
        event_type="on-select",
        caption="Select metric",
        clear_behavior="keep-current",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "filter",
        source_sheet="Selector",
        target_sheet="Selector",
        field_mappings={"True": "False"},
        event_type="on-select",
        caption="Deselect metric",
        clear_behavior="show-all",
    )
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
