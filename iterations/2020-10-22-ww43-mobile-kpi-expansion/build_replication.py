"""Native parameter-driven expansion in a narrow default vertical dashboard."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_10_21_WW43_Mobile_KPIs"
METRICS = ["SALES", "PROFIT", "MARGIN", "CUSTOMERS"]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    e.add_parameter(
        "Selected Measure", datatype="string", default_value="", domain_type="any"
    )
    for name, formula, dtype, role, ftype in [
        ("SALES", "[Sales]", "real", "measure", "quantitative"),
        ("PROFIT", "[Profit]", "real", "measure", "quantitative"),
        ("MARGIN", "SUM([Profit])/SUM([Sales])", "real", "measure", "quantitative"),
        ("CUSTOMERS", "COUNTD([Customer ID])", "integer", "measure", "quantitative"),
        (
            "Baseline Date",
            "DATETRUNC('month',MAKEDATE(2019,MONTH([Order Date]),DAY([Order Date])))",
            "datetime",
            "dimension",
            "ordinal",
        ),
        (
            "FILTER - Selected Measure",
            "[Selected Measure]",
            "string",
            "dimension",
            "nominal",
        ),
        ("True", "TRUE", "boolean", "dimension", "nominal"),
        ("False", "FALSE", "boolean", "dimension", "nominal"),
        ("Value Axis", "MIN(1)", "integer", "measure", "quantitative"),
        ("Heading Axis", "MIN(0)", "integer", "measure", "quantitative"),
    ]:
        e.add_calculated_field(
            name, formula, datatype=dtype, role=role, field_type=ftype
        )
    for metric in METRICS:
        e.set_field_format(
            metric,
            "p0.0%"
            if metric == "MARGIN"
            else "n#,##0"
            if metric == "CUSTOMERS"
            else 'c"$"#,##0;-"$"#,##0',
        )
        name = "Customer" if metric == "CUSTOMERS" else metric.title()
        e.add_calculated_field(
            name + " Icon",
            f"IF [Selected Measure]='{metric}' THEN '\u25ac' ELSE '\u271a' END",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        e.add_calculated_field(
            name + " - String to pass",
            f"IF [Selected Measure]<>'{metric}' THEN '{metric}' ELSE '' END",
            datatype="string",
            role="dimension",
            field_type="nominal",
        )
        kpi = "KPI - " + name
        bar = "Bar - " + ("Customers" if metric == "CUSTOMERS" else name)
        expression = "SUM(" + metric + ")" if metric in ["SALES", "PROFIT"] else metric
        for sheet in [kpi, bar]:
            e.add_worksheet(sheet)
            e.set_worksheet_title(sheet, "")
        detail = [name + " - String to pass", "True", "False"]
        e.configure_layered_chart(
            kpi,
            columns=["Value Axis", "Heading Axis"],
            axis_shelf="columns",
            panes=[
                {
                    "axis": "Value Axis",
                    "mark_type": "Bar",
                    "labels": [expression],
                    "detail_extra": detail,
                    "label_runs": [
                        {
                            "field": expression,
                            "fontsize": 14,
                            "bold": False,
                            "fontname": "Tableau Book",
                            "fontcolor": "#1b1b1b",
                        }
                    ],
                    "cell_style": {"text-align": "right", "vertical-align": "center"},
                    "mark_style": {
                        "mark-color": "#e6e6e6",
                        "size": "1.9560221433639526",
                        "has-stroke": "false",
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                    },
                },
                {
                    "axis": "Heading Axis",
                    "mark_type": "GanttBar",
                    "labels": [name + " Icon"],
                    "detail_extra": detail,
                    "label_runs": [
                        {
                            "field": name + " Icon",
                            "fontname": "Tableau Book",
                            "fontsize": 14,
                            "fontcolor": "#555555",
                        },
                        {
                            "text": " "
                            + metric
                            + (" (%)" if metric == "MARGIN" else ""),
                            "fontname": "Tableau Book",
                            "fontsize": 14,
                            "bold": False,
                            "fontcolor": "#555555",
                        },
                    ],
                    "cell_style": {"text-align": "left", "vertical-align": "center"},
                    "mark_style": {
                        "mark-color": "#e6e6e6",
                        "size": "1.9560221433639526",
                        "has-stroke": "false",
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                    },
                },
            ],
            synchronized=True,
            fold_axes=True,
        )
        e.configure_worksheet_style(
            kpi,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            disable_tooltip=True,
            axis_style={
                "render-fold-reversed": "true",
                "encodings": [
                    {
                        "field": "Value Axis",
                        "scope": "cols",
                        "type": "space",
                        "attr": "space",
                        "class": "0",
                        "field-type": "quantitative",
                        "range-type": "fixed",
                        "min": 0,
                        "max": 1,
                    }
                ],
            },
            cell_formats=[{"height": 52}],
        )
        e.configure_layered_chart(
            bar,
            columns=["EXACTDATE(Baseline Date)"],
            rows=[expression],
            panes=[
                {
                    "axis": expression,
                    "mark_type": "Bar",
                    "labels": [expression],
                    "label_runs": [
                        {"field": expression, "fontsize": 10, "fontcolor": "#555555"}
                    ],
                    "mark_style": {
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                        "mark-color": "#4e79a7",
                        "has-stroke": "false",
                        "size": "1.9890055656433105",
                    },
                }
            ],
            filters=[{"column": "FILTER - Selected Measure", "values": [metric]}],
        )
        encodings = [
            {
                "field": "EXACTDATE(Baseline Date)",
                "scope": "cols",
                "type": "space",
                "attr": "space",
                "class": "0",
                "field-type": "quantitative",
                "major-origin": "#2018-12-01 00:00:00#",
                "major-spacing": "2.0",
                "major-units": "months",
                "minor-show": "false",
            }
        ]
        if metric != "CUSTOMERS":
            encodings.append(
                {
                    "field": expression,
                    "scope": "rows",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": 0,
                    "max": {"SALES": 550000, "PROFIT": 70000, "MARGIN": 0.22}[metric],
                }
            )
        e.configure_worksheet_style(
            bar,
            pane_datalabel_style={
                "color-mode": "user",
                "color": "#555555",
                **(
                    {"text-orientation": "-90"} if metric in ["SALES", "PROFIT"] else {}
                ),
            },
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
            label_formats=[
                {"field": "EXACTDATE(Baseline Date)", "text-format": "*mmmmm"}
            ],
            axis_style={
                "encodings": encodings,
                "per_field": [
                    {
                        "field": expression,
                        "scope": "rows",
                        "class": 0,
                        "attr": "display",
                        "value": "false",
                    },
                    {
                        "field": "EXACTDATE(Baseline Date)",
                        "scope": "cols",
                        "class": 0,
                        "attr": "title",
                        "value": "",
                    },
                ],
                "per_scope": {
                    "cols": {"stroke-color": "#555555", "tick-color": "#555555"}
                },
            },
        )
    children = []
    for metric in METRICS:
        name = "Customer" if metric == "CUSTOMERS" else metric.title()
        children.extend(
            [
                {
                    "type": "worksheet",
                    "name": "KPI - " + name,
                    "fixed_size": 52,
                    "fit": "entire",
                    "show_title": False,
                    "style": {
                        "margin": 4,
                        "margin-top": 10,
                        "margin-right": 10,
                        "margin-bottom": 0,
                        "margin-left": 10,
                    },
                },
                {
                    "type": "worksheet",
                    "name": "Bar - " + ("Customers" if metric == "CUSTOMERS" else name),
                    "fit": "entire",
                    "show_title": False,
                    "style": {
                        "margin": 4,
                        "margin-top": 10,
                        "margin-right": 10,
                        "margin-bottom": 0,
                        "margin-left": 10,
                    },
                },
            ]
        )
    children.append(
        {
            "type": "container",
            "direction": "horizontal",
            "fixed_size": 42,
            "children": [
                {
                    "type": "text",
                    "text": "DESIGNED BY : LUKE STANKE\nRECREATED WITH CWTWB",
                    "runs": [
                        {
                            "text": "DESIGNED BY : LUKE STANKE\nRECREATED WITH CWTWB",
                            "font_size": 8,
                            "font_color": "#666666",
                            "font_alignment": "0",
                        }
                    ],
                    "font_size": 8,
                },
                {
                    "type": "text",
                    "text": "#WOW2020 | WEEK43",
                    "runs": [
                        {
                            "text": "#WOW2020 | WEEK43",
                            "font_size": 8,
                            "font_color": "#666666",
                            "font_alignment": "2",
                        }
                    ],
                },
            ],
        }
    )
    e.add_dashboard(
        DASHBOARD,
        width=400,
        height=600,
        layout={
            "type": "container",
            "direction": "vertical",
            "style": {"margin": 0},
            "children": [
                {
                    "type": "text",
                    "fixed_size": 46,
                    "style": {
                        "padding": 10,
                        "margin": 0,
                        "background-color": "#ffffff",
                    },
                    "runs": [
                        {
                            "text": "MOBILE CHALLENGE",
                            "font_size": 16,
                            "font_name": "Tableau Medium",
                            "bold": True,
                            "font_color": "#0070a0",
                            "font_alignment": "0",
                        }
                    ],
                },
                {
                    "type": "container",
                    "direction": "vertical",
                    "style": {"background-color": "#f5f5f5"},
                    "children": children,
                },
            ],
        },
    )
    for metric in METRICS:
        name = "Customer" if metric == "CUSTOMERS" else metric.title()
        sheet = "KPI - " + name
        e.add_dashboard_action(
            DASHBOARD,
            "parameter",
            source_sheet=sheet,
            source_field=name + " - String to pass",
            target_parameter="Selected Measure",
            event_type="on-select",
            caption="Toggle " + metric,
            aggregation="attr",
            clear_behavior="keep-current",
        )
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"True": "False"},
            event_type="on-select",
            caption="Deselect " + metric,
        )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
