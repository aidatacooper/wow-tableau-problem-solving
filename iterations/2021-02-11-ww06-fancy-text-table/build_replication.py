"""Build the eight-measure monthly report from locked raw Hyper, using public SDK."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_02_11_WW06_Formatted_Table"
MEASURES = [
    "SUM(CY SALES)",
    "SUM(LY SALES)",
    "CY vs LY",
    "△",
    "% DIFF",
    "SUM(BEST DAY)",
    "SUM(WORST DAY)",
    "RANK",
]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/superstore.hyper"))
    definitions = [
        (
            "Current Year",
            "YEAR({MAX([Order Date])})",
            "integer",
            "dimension",
            "ordinal",
            "",
        ),
        ("Last Year", "[Current Year]-1", "integer", "dimension", "ordinal", ""),
        (
            "CY SALES",
            "IF YEAR([Order Date])=[Current Year] THEN [Sales] END",
            "real",
            "measure",
            "quantitative",
            'n"$"#,##0;-"$"#,##0',
        ),
        (
            "LY SALES",
            "IF YEAR([Order Date])=[Last Year] THEN [Sales] END",
            "real",
            "measure",
            "quantitative",
            'n"$"#,##0;-"$"#,##0',
        ),
        (
            "Order Month",
            "DATENAME('month',[Order Date])",
            "string",
            "dimension",
            "nominal",
            "",
        ),
        (
            "CY vs LY",
            "IF SUM([CY SALES])>SUM([LY SALES]) THEN 1 ELSE -1 END",
            "integer",
            "measure",
            "quantitative",
            "*✅;❌; ▬",
        ),
        (
            "△",
            "SUM([CY SALES])-SUM([LY SALES])",
            "real",
            "measure",
            "quantitative",
            '*"$"#,##0;-"$"#,##0',
        ),
        (
            "% DIFF",
            "[△]/SUM([LY SALES])",
            "real",
            "measure",
            "quantitative",
            "*+0.0%;-0.0%",
        ),
        (
            "Sales Per Day",
            "{FIXED [Order Date]: SUM([CY SALES])}",
            "real",
            "measure",
            "quantitative",
            "",
        ),
        (
            "Max CY Sales Per Month",
            "{FIXED [Order Month]: MAX([Sales Per Day])}",
            "real",
            "measure",
            "quantitative",
            "",
        ),
        (
            "Min CY Sales Per Month",
            "{FIXED [Order Month]: MIN([Sales Per Day])}",
            "real",
            "measure",
            "quantitative",
            "",
        ),
        (
            "BEST DAY",
            "INT({FIXED [Order Month]: MAX(IF [Sales Per Day]=[Max CY Sales Per Month] THEN [Order Date] END)})+2",
            "integer",
            "measure",
            "quantitative",
            "*dd mmm yyyy",
        ),
        (
            "WORST DAY",
            "INT({FIXED [Order Month]: MAX(IF [Sales Per Day]=[Min CY Sales Per Month] THEN [Order Date] END)})+2",
            "integer",
            "measure",
            "quantitative",
            "*dd mmm yyyy",
        ),
        ("Number of Months", "SIZE()", "integer", "measure", "quantitative", ""),
        (
            "RANK",
            "IF RANK(SUM([CY SALES]))<=[Number of Months]/2 THEN 1 ELSE -1 END",
            "integer",
            "measure",
            "quantitative",
            '*"TOP";"BOTTOM"',
        ),
    ]
    for name, formula, datatype, role, field_type, default_format in definitions:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format=default_format,
            table_calc="Columns" if name in {"Number of Months", "RANK"} else None,
        )
    editor.add_worksheet("Table")
    editor.configure_chart(
        "Table",
        mark_type="Text",
        rows=["Order Month"],
        measure_values=MEASURES,
        color="Multiple Values",
        separate_measure_domains=True,
        label_runs=[{"field": "Multiple Values", "bold": True}],
        table_calc_overrides={
            "RANK": [
                {"ordering_type": "Columns"},
                {"field": "Number of Months", "ordering_type": "Columns"},
            ]
        },
    )
    editor.set_worksheet_rich_title(
        "Table",
        [
            {
                "text": "SALES PROGRESS REPORT",
                "bold": True,
                "fontname": "Tableau Medium",
                "fontsize": 14,
            }
        ],
    )
    editor.configure_worksheet_style(
        "Table",
        disable_tooltip=True,
        hide_row_field_labels=True,
        hide_sort_controls=True,
        table_formats=[{"attr": "font-size", "value": 11}],
        cell_formats=[{"field": "Order Month", "height": 51}],
        pane_cell_style={"vertical-align": "center", "text-align": "center"},
    )
    for field in MEASURES:
        if field in {"SUM(CY SALES)", "SUM(LY SALES)", "△"}:
            settings = {"colors": ["#000000", "#000000"], "min": 0, "max": 0}
        elif field == "SUM(BEST DAY)":
            settings = {"colors": ["#00aa00", "#00aa00"], "min": 0, "max": 0}
        elif field == "SUM(WORST DAY)":
            settings = {"colors": ["#ff0000", "#ff0000"], "min": 100000, "max": 1000000}
        else:
            settings = {"colors": ["#ff0000", "#00aa00"], "center": 0}
        editor.configure_worksheet_style(
            "Table", color_style={"field": field, "num_steps": 2, **settings}
        )
    footer = [
        {
            "type": "text",
            "text": "CHALLENGE BY : ANN JACKSON",
            "font_color": "#da020e",
            "font_size": 8,
            "bold": True,
            "absolute": {"x": 667, "y": 91000, "w": 32888, "h": 4000},
        },
        {
            "type": "text",
            "text": "#WOW2021  |  WEEK 6",
            "font_color": "#da020e",
            "font_size": 8,
            "bold": True,
            "align": "center",
            "absolute": {"x": 33555, "y": 91000, "w": 32890, "h": 4000},
        },
        {
            "type": "text",
            "text": "RECREATED WITH CWTWB",
            "font_color": "#da020e",
            "font_size": 8,
            "bold": True,
            "align": "right",
            "absolute": {"x": 66445, "y": 91000, "w": 32888, "h": 4000},
        },
        {
            "type": "text",
            "text": "https://www.workout-wednesday.com/2021w06tab/",
            "url": "https://www.workout-wednesday.com/2021w06tab/",
            "font_color": "#da020e",
            "font_size": 8,
            "align": "center",
            "absolute": {"x": 667, "y": 95000, "w": 98666, "h": 4000},
        },
    ]
    for index, node in enumerate(footer):
        node["runs"] = [
            {
                "text": node["text"],
                "font_color": node["font_color"],
                "font_size": node["font_size"],
                "font_name": "Tableau Medium",
                "bold": node.get("bold", False),
                "font_alignment": [0, 1, 2, 1][index],
            }
        ]
        node["style"] = {"margin": "4"}
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=800,
        worksheet_names=["Table"],
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": "8"},
            "children": [
                {
                    "type": "worksheet",
                    "name": "Table",
                    "fit": "entire",
                    "style": {"margin": "4"},
                    "absolute": {"x": 667, "y": 1000, "w": 98666, "h": 90000},
                },
                *footer,
            ],
        },
    )
    editor.set_active_dashboard(DASHBOARD)
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
