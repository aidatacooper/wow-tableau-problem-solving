"""Native daily-profit waterfall; only extracted data and public SDK APIs."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_10_28_WW44_Waterfall_Small_Multiple"
PALETTE = {"Blue": "#a0cbe8", "Red": "#e15759", "Grey": "#b3b7b8"}


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    editor.add_calculated_field(
        "Cols",
        "IF MONTH([Order Date])%3=0 THEN 3 ELSE MONTH([Order Date])%3 END",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    for name, formula in {
        "Profit for Month": "{FIXED YEAR([Order Date]),MONTH([Order Date]): SUM([Profit])}",
        "Max Monthly Profit in Year": "{FIXED YEAR([Order Date]): MAX([Profit for Month])}",
        "Actual Profit": "ZN(SUM([Profit]))",
        "Negative Profit": "SUM([Profit])*-1",
        "Running Profit": "RUNNING_SUM(SUM([Profit]))",
    }.items():
        editor.add_calculated_field(
            name,
            formula,
            datatype="real",
            role="measure",
            table_calc="Rows" if name == "Running Profit" else None,
            default_format='c"$"#,##0;-"$"#,##0',
        )
    editor.add_calculated_field(
        "Colour",
        "IF SUM([Profit])<0 THEN 'Red' ELSEIF SUM([Profit])>0 THEN 'Blue' ELSE 'Grey' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    editor.set_datasource_color_palette("Colour", PALETTE)
    filters = [{"column": "YEAR(Order Date)", "values": [2020]}]
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["YEAR(Order Date)", "Cols", "DAY(Order Date)"],
        rows=[
            "QUARTER(Order Date)",
            "Running Profit",
            "SUM(Max Monthly Profit in Year)",
        ],
        filters=filters,
        synchronized=True,
        fold_axes=True,
        table_calc_context=True,
        table_calc_overrides={
            "Running Profit": [
                {"ordering_type": "Field", "ordering_field": "DAY(Order Date)"}
            ]
        },
        panes=[
            {
                "axis": "Running Profit",
                "mark_type": "GanttBar",
                "color": "Colour",
                "color_map": PALETTE,
                "size": "Negative Profit",
                "detail": "MONTH(Order Date)",
                "tooltip": ["Actual Profit", "ATTR(Order Date)", "Running Profit"],
                "mark_style": {"has-stroke": "false", "mark-labels-show": "false"},
            },
            {
                "axis": "SUM(Max Monthly Profit in Year)",
                "mark_type": "Line",
                "labels": ["MONTH(Order Date)", "SUM(Profit for Month)"],
                "label_runs": [
                    {"field": "MONTH(Order Date)"},
                    {"text": "\n"},
                    {"field": "SUM(Profit for Month)"},
                ],
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "line-ends",
                    "mark-labels-line-first": "true",
                    "mark-labels-line-last": "false",
                    "mark-transparency": "0",
                    "has-stroke": "false",
                },
                "datalabel_style": {"font-size": 10, "color": "#000000"},
                "cell_style": {"text-align": "right", "vertical-align": "bottom"},
            },
        ],
    )
    editor.configure_worksheet_domain_range("Chart", ["[Order Date]"])
    editor.configure_subtotals(
        "Chart",
        measure_fields=[
            "Running Profit",
            "Negative Profit",
            "Profit for Month",
            "Max Monthly Profit in Year",
        ],
        aggregation="Automatic",
        subtotal_fields=["Cols"],
        label="Total",
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_axes=True,
        hide_gridlines=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        label_formats=[
            {"field": f, "display": "false"} for f in ["Cols", "DAY(Order Date)"]
        ],
        table_dividers=[
            {"scope": scope, "stroke-color": "#f5f5f5"} for scope in ["rows", "cols"]
        ],
        header_formats=[
            {"field": "QUARTER(Order Date)", "attr": "width", "value": "40"}
        ],
    )
    editor.set_worksheet_title("Chart", "")
    editor.add_calculated_field(
        "Running Actual Profit",
        "RUNNING_SUM([Actual Profit])",
        datatype="real",
        role="measure",
        table_calc="Columns",
        default_format="n#,##0.0000",
    )
    editor.add_worksheet("Data")
    editor.configure_layered_chart(
        "Data",
        rows=[
            "QUARTER(Order Date)",
            "MONTH(Order Date)",
            "DISCRETE(DAYTRUNC(Order Date))",
        ],
        columns=["Measure Names"],
        axis_shelf="columns",
        filters=filters,
        table_calc_context=True,
        table_calc_overrides={
            "Running Profit": [
                {
                    "ordering_type": "Field",
                    "ordering_field": "DISCRETE(DAYTRUNC(Order Date))",
                }
            ],
            "Running Actual Profit": [{"ordering_type": "Columns"}],
        },
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    "SUM(Profit)",
                    "Running Profit",
                    "SUM(Profit for Month)",
                    "SUM(Max Monthly Profit in Year)",
                    "Actual Profit",
                    "Running Actual Profit",
                ],
            }
        ],
    )
    editor.configure_worksheet_domain_range("Data", ["[Order Date]"])
    editor.configure_subtotals(
        "Data",
        measure_fields=[
            "Profit",
            "Running Profit",
            "Profit for Month",
            "Max Monthly Profit in Year",
            "Actual Profit",
            "Running Actual Profit",
        ],
        aggregation="Automatic",
        subtotal_fields=["MONTH(Order Date)"],
        label="Total",
    )
    editor.add_dashboard(
        DASHBOARD,
        width=900,
        height=800,
        worksheet_names=["Chart"],
        layout={
            "type": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "Can you build a Small Multiple Waterfall Chart?",
                    "font_size": 16,
                    "font_color": "#000000",
                    "alignment": "center",
                    "fixed_size": 44,
                },
                {
                    "type": "worksheet",
                    "name": "Chart",
                    "show_title": False,
                    "fit": "entire",
                },
                {
                    "type": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "text": "DESIGNED BY : LORNA BROWN",
                            "font_size": 8,
                        },
                        {
                            "type": "text",
                            "text": "#WOW2020 | WEEK 44",
                            "font_size": 8,
                            "alignment": "center",
                        },
                        {
                            "type": "text",
                            "text": "DONNA COLES REFERENCE | CWTWB",
                            "font_size": 8,
                            "alignment": "right",
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "http://www.workout-wednesday.com/2020w44/",
                    "font_size": 8,
                    "alignment": "center",
                    "fixed_size": 32,
                },
            ],
        },
    )
    editor.enable_automatic_phone_layout(DASHBOARD)
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
