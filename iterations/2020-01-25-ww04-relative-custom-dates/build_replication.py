"""Rebuild relative/custom dates using extracted Hyper and public SDK APIs."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_01_22_WW04_Relative_and_Custom_Dates"
CHOICES = ["Last 14 Days", "Last 30 Days", "Last N Days", "Custom Dates"]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    for name, datatype, value in [
        ("Date Selector", "string", CHOICES[0]),
        ("N Days", "integer", "60"),
        ("Start Date", "date", "#2019-01-01#"),
        ("End Date", "date", "#2019-12-31#"),
    ]:
        editor.add_parameter(name, datatype, value, domain_type="any")
    calculations = [
        ("Latest Date", "{FIXED:MAX([Order Date])}", "date", "dimension"),
        (
            "In Timeframe",
            "CASE [Date Selector] WHEN 'Last 14 Days' THEN [Order Date]>DATEADD('day',-14,[Latest Date]) WHEN 'Last 30 Days' THEN [Order Date]>DATEADD('day',-30,[Latest Date]) WHEN 'Last N Days' THEN [Order Date]>DATEADD('day',-1*[N Days],[Latest Date]) ELSE [Order Date]>=[Start Date] AND [Order Date]<=[End Date] END",
            "boolean",
            "dimension",
        ),
        ("Profit Ratio", "SUM([Profit])/SUM([Sales])", "real", "measure"),
        ("True", "TRUE", "boolean", "dimension"),
        ("False", "FALSE", "boolean", "dimension"),
        ("Show N Days", "[Date Selector]='Last N Days'", "boolean", "dimension"),
        ("Show Custom Dates", "[Date Selector]='Custom Dates'", "boolean", "dimension"),
    ]
    for name, formula, datatype, role in calculations:
        editor.add_calculated_field(name, formula, datatype=datatype, role=role)
    for field in ["Sales", "Profit"]:
        editor.set_field_format(field, 'c"$"#,##0;-"$"#,##0')
    editor.set_field_format("Profit Ratio", "p0.0%")
    for name in ["Selector", "BANs", "Sales trend"]:
        editor.add_worksheet(name)
    panes = []
    for i, choice in enumerate(CHOICES):
        editor.add_calculated_field(choice, "MIN(0)", datatype="integer")
        editor.add_calculated_field(
            f"Selected {i}",
            f"[Date Selector]='{choice}'",
            datatype="boolean",
            role="dimension",
        )
        editor.add_calculated_field(
            f"Indicator {i}",
            f"IF [Date Selector]='{choice}' THEN '●' ELSE '○' END",
            datatype="string",
            role="dimension",
        )
        panes.append(
            {
                "axis": choice,
                "mark_type": "Text",
                "labels": ["Measure Names", f"Indicator {i}"],
                "detail_extra": ["True", "False"],
                "label_runs": [
                    {"field": f"Indicator {i}", "fontcolor": "#049da5", "fontsize": 16},
                    {"text": " " + choice, "fontsize": 10},
                ],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
        )
    editor.configure_layered_chart(
        "Selector",
        columns=CHOICES,
        panes=panes,
        axis_shelf="columns",
        fold_axes=False,
        hide_axes=True,
    )
    editor.configure_worksheet_style(
        "Selector",
        axis_style={
            "encodings": [
                {
                    "field": choice,
                    "scope": "cols",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": -1,
                    "max": 1,
                }
                for choice in CHOICES
            ]
        },
    )
    filters = [{"column": "In Timeframe", "values": [True]}]
    editor.configure_layered_chart(
        "BANs",
        columns=["Measure Names"],
        filters=filters,
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "labels": ["Measure Names"],
                "measure_values": ["SUM(Sales)", "Profit Ratio", "SUM(Profit)"],
                "label_runs": [
                    {
                        "field": "Multiple Values",
                        "bold": True,
                        "fontsize": 14,
                        "fontcolor": "#049da5",
                    },
                    {"text": "\n"},
                    {
                        "field": "Measure Names",
                        "italic": True,
                        "fontsize": 10,
                        "fontcolor": "#049da5",
                    },
                ],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
        ],
    )
    editor.configure_worksheet_style(
        "BANs",
        label_formats=[{"field": "Measure Names", "display": "false"}],
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"color": "#049da5"},
    )
    editor.configure_dual_axis(
        "Sales trend",
        columns=["DAYTRUNC(Order Date)"],
        rows=["SUM(Sales)", "SUM(Sales)"],
        mark_type_1="Area",
        mark_type_2="Line",
        synchronized=True,
        filters=filters,
        mark_color_1="#049da5",
        mark_color_2="#049da5",
        mark_sizing_off=True,
        show_labels=False,
    )
    editor.configure_worksheet_style(
        "Sales trend",
        panes_style={
            "1": {"mark_style": {"mark-transparency": "65"}},
            "2": {"mark_style": {"size": "0.45"}},
        },
        axis_style={
            "per_field": [
                {
                    "field": "DAYTRUNC(Order Date)",
                    "scope": "cols",
                    "attr": "title",
                    "value": "",
                },
                {"field": "SUM(Sales)", "scope": "rows", "attr": "title", "value": ""},
                {
                    "field": "SUM(Sales)",
                    "scope": "rows",
                    "class": "1",
                    "attr": "display",
                    "value": "false",
                },
            ]
        },
    )
    for sheet in ["Selector", "BANs", "Sales trend"]:
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_col_field_labels=True,
            hide_row_field_labels=True,
            hide_sort_controls=True,
        )
    editor.configure_worksheet_style("Selector", disable_tooltip=True)

    def position(x, y, w, h):
        return {
            "x": round(x / 1100 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1100 * 100000),
            "h": round(h / 800 * 100000),
        }

    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2020 | WEEK 4 | Can you combine relative and custom date ranges?",
                    "font_color": "#049da5",
                    "font_size": 12,
                    "bold": True,
                }
            ],
            "absolute": position(8, 8, 1084, 42),
        },
        {
            "type": "worksheet",
            "name": "Selector",
            "show_title": False,
            "fit": "entire",
            "absolute": position(8, 50, 775, 100),
        },
        {
            "type": "paramctrl",
            "parameter": "N Days",
            "mode": "type_in",
            "caption": "N Days",
            "visibility": {"field": "Show N Days", "initially_visible": False},
            "absolute": position(245, 147, 150, 30),
        },
        {
            "type": "container",
            "direction": "horizontal",
            "visibility": {"field": "Show Custom Dates", "initially_visible": False},
            "absolute": position(800, 54, 290, 65),
            "children": [
                {"type": "paramctrl", "parameter": "Start Date", "mode": "datetime"},
                {"type": "paramctrl", "parameter": "End Date", "mode": "datetime"},
            ],
        },
        {
            "type": "worksheet",
            "name": "BANs",
            "show_title": False,
            "fit": "entire",
            "absolute": position(8, 180, 1084, 67),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "Sales trend",
                    "font_size": 12,
                    "bold": True,
                    "font_alignment": "1",
                }
            ],
            "style": {"background-color": "#f5f5f5"},
            "absolute": position(8, 248, 1084, 30),
        },
        {
            "type": "worksheet",
            "name": "Sales trend",
            "show_title": False,
            "fit": "entire",
            "absolute": position(8, 278, 1084, 448),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "DESIGNED BY : SEAN MILLER                         #WOW2020 | WEEK 4                         RECREATED WITH CWTWB",
                    "font_color": "#049da5",
                    "font_size": 8,
                    "bold": True,
                }
            ],
            "absolute": position(8, 730, 1084, 30),
        },
        {
            "type": "text",
            "text": "http://www.workout-wednesday.com/2020w04/",
            "absolute": position(350, 764, 450, 25),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1100,
        height=800,
        worksheet_names=["Selector", "BANs", "Sales trend"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "parameter",
        source_sheet="Selector",
        source_field="Measure Names",
        target_parameter="Date Selector",
        caption="Date Selector",
        event_type="on-select",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "filter",
        source_sheet="Selector",
        target_sheet="Selector",
        field_mappings={"True": "False"},
        caption="Deselect selector",
        event_type="on-select",
        clear_behavior="show-all",
    )
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
