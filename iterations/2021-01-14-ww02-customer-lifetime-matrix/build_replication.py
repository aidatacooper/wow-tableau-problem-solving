"""Build the cohort matrix from locked raw orders through public SDK APIs."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_01_13_WW02_Customer_Lifetime_Matrix"
COHORT = "ACQUISITION QUARTER"
CUSTOMERS = "CUSTOMERS"
AGE = "QUARTERS SINCE BIRTH"
AVG = "Avg Lifetime Value"
VALUE = "CUSTOMER LIFETIME VALUE (CLTV)"


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    e.add_calculated_field(
        COHORT,
        "DATE(DATETRUNC('quarter',{FIXED [Customer ID] : MIN([Order Date])}))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        CUSTOMERS,
        "{FIXED [ACQUISITION QUARTER]: COUNTD([Customer ID])}",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        AGE,
        "DATEDIFF('quarter',[ACQUISITION QUARTER],DATETRUNC('quarter',[Order Date]))",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        AVG,
        "RUNNING_SUM(SUM([Sales])) / SUM([CUSTOMERS])",
        datatype="real",
        table_calc="Rows",
    )
    e.add_calculated_field(
        VALUE,
        "IF ISNULL([Avg Lifetime Value]) AND NOT ISNULL(LOOKUP([Avg Lifetime Value],-1)) AND NOT ISNULL(LOOKUP([Avg Lifetime Value],1)) THEN LOOKUP([Avg Lifetime Value],-1) ELSE [Avg Lifetime Value] END",
        datatype="real",
        table_calc="Rows",
    )
    e.set_field_format(COHORT, '* "Q"q yyyy')
    for field in (AVG, VALUE):
        e.set_field_format(field, 'c"$"#,##0;-"$"#,##0')
    e.add_worksheet("Viz")
    e.configure_layered_chart(
        "Viz",
        columns=[AGE],
        rows=["[" + COHORT + "]", CUSTOMERS],
        panes=[
            {
                "mark_type": "Square",
                "color": VALUE,
                "labels": [VALUE],
                "tooltip": ["[" + COHORT + "]", CUSTOMERS, AGE, VALUE],
                "mark_style": {
                    "mark-labels-cull": "true",
                    "mark-labels-show": "true",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                },
            }
        ],
        filters=[
            {
                "column": VALUE,
                "type": "quantitative",
                "min": "32.357500000000002",
                "max": "3353.0410818181813",
            }
        ],
        table_calc_overrides={
            VALUE: [
                {
                    "ordering_type": "Field",
                    "order": [{"field": AGE, "reference": "instance"}],
                },
                {
                    "field": AVG,
                    "ordering_type": "Field",
                    "order": [{"field": AGE, "reference": "instance"}],
                },
            ]
        },
        table_calc_context=False,
    )
    e.configure_custom_tooltip(
        "Viz",
        [
            {"field": "[" + COHORT + "]", "bold": True},
            {"text": "\nCUSTOMER LIFETIME VALUE (CLTV):\t"},
            {"field": VALUE, "bold": True},
            {"text": "\nTOTAL CUSTOMERS:\t"},
            {"field": CUSTOMERS, "bold": True},
            {"text": "\nQUARTERS SINCE BIRTH:\t"},
            {"field": AGE, "bold": True},
            {"text": "\n\nAfter ", "italic": True},
            {"field": AGE, "bold": True, "italic": True},
            {"text": " quarter(s), customers acquired in ", "italic": True},
            {"field": "[" + COHORT + "]", "bold": True, "italic": True},
            {"text": " are worth an average of ", "italic": True},
            {"field": VALUE, "bold": True, "italic": True},
            {"text": " each.", "italic": True},
        ],
    )
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_borders=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_sort_controls=True,
        color_style={
            "field": VALUE,
            "colors": [
                "#fff7fb",
                "#ece2f0",
                "#d0d1e6",
                "#a6bddb",
                "#67a9cf",
                "#3690c0",
                "#02818a",
                "#016c59",
                "#014636",
            ],
        },
        cell_formats=[{"field": CUSTOMERS, "height": 61}],
        header_formats=[
            {"field": CUSTOMERS, "width": 120},
            {"field": "[" + COHORT + "]", "width": 184},
            {"field": AGE, "height": 35},
        ],
        label_formats=[
            {
                "field": field,
                "font-family": "Tableau Medium",
                "text-align": "center",
                "color": "#333333",
            }
            for field in ["[" + COHORT + "]", CUSTOMERS]
        ],
        pane_datalabel_style={"font-size": 10, "text-align": "center"},
    )
    e.set_worksheet_title("Viz", "")
    e.add_dashboard(
        DASHBOARD,
        width=1400,
        height=1000,
        layout={
            "type": "container",
            "direction": "vertical",
            "style": {"margin": 8},
            "children": [
                {
                    "type": "text",
                    "fixed_size": 67,
                    "runs": [
                        {
                            "text": "CUSTOMER LIFETIME VALUE (CLTV) MATRIX\n",
                            "bold": True,
                            "font_size": 19,
                            "font_alignment": 0,
                        },
                        {
                            "text": "CUSTOMERS ARE GROUPED BY THE QUARTER THEY WERE ACQUIRED",
                            "bold": True,
                            "font_size": 13,
                            "font_alignment": 0,
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
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "CHALLENGE BY : ANN JACKSON",
                                    "font_size": 8,
                                    "font_alignment": 0,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "#WOW2021  | WEEK 02",
                                    "font_size": 8,
                                    "font_alignment": 1,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "RECREATED WITH CWTWB",
                                    "font_size": 8,
                                    "font_alignment": 2,
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "fixed_size": 32,
                    "runs": [
                        {
                            "text": "http://www.workout-wednesday.com/2021w02tab/",
                            "font_size": 8,
                            "font_alignment": 1,
                            "font_color": "#3690c0",
                            "hyperlink": "http://www.workout-wednesday.com/2021w02tab/",
                        }
                    ],
                },
            ],
        },
    )
    e.set_window_state("Viz", zoom_entire_view=True)
    e.set_window_state(DASHBOARD, maximized=True, zoom_entire_view=True)
    target = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    e.save(str(target))
    return target


if __name__ == "__main__":
    print(build())
