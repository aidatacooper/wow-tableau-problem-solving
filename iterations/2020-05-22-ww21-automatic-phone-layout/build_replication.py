"""Six-sheet annual sales/profit dashboard with native automatic phone layout."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_05_19_WW21_Auto_Phone_Layout"
SHEETS = [
    "Sales Summary",
    "Sales Line",
    "Top 10 Products by Sales",
    "Profit Summary",
    "Profit Line",
    "Top & Bottom 10 Products by Profit",
]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/TEMP_151xfqm0kt34qz10esqhe11mmnal.hyper")
    )
    colors = {"2018": "#67737c", "2019": "#7c4d79"}
    for name, basis, direction in [
        ("Top 10 Products by Sales", "Sales", "DESC"),
        ("Top 10 Products by Profit", "Profit", "DESC"),
        ("Bottom 10 Products by Profit", "Profit", "ASC"),
    ]:
        editor.add_set(
            name, "Product Name", basis_field=basis, top_n=10, direction=direction
        )
    editor.add_combined_set(
        "Top & Bottom Products by Profit",
        ["Top 10 Products by Profit", "Bottom 10 Products by Profit"],
    )
    for name, formula in [
        ("Show Top Sales", "[Top 10 Products by Sales]"),
        ("Show Extreme Profit", "[Top & Bottom Products by Profit]"),
    ]:
        editor.add_calculated_field(
            name, formula, datatype="boolean", role="dimension", field_type="nominal"
        )
    editor.add_calculated_field(
        "Profit Group",
        "IF [Top 10 Products by Profit] THEN 'Top 10' ELSE 'Bottom 10' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Has Previous Year",
        "NOT ISNULL(LOOKUP(SUM([Sales]),-1))",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
        table_calc="Rows",
    )
    for metric in ["Sales", "Profit"]:
        editor.set_field_format(metric, 'c"$"#,##0;-"$"#,##0')
        change = metric + " Year Change"
        editor.add_calculated_field(
            change,
            "(SUM(["
            + metric
            + "])-LOOKUP(SUM(["
            + metric
            + "]),-1))/ABS(LOOKUP(SUM(["
            + metric
            + "]),-1))",
            table_calc="Rows",
        )
        editor.set_field_format(change, "p0%")
        sheet = metric + " Line"
        editor.add_worksheet(sheet)
        editor.configure_layered_chart(
            sheet,
            columns=["MONTH(Order Date)"],
            rows=["SUM(" + metric + ")"],
            panes=[
                {
                    "axis": "SUM(" + metric + ")",
                    "mark_type": "Line",
                    "color": "YEAR(Order Date)",
                    "color_map": colors,
                }
            ],
            filters=[
                {
                    "column": "YEAR(Order Date)",
                    "values": [2018, 2019],
                    "type": "categorical",
                }
            ],
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_borders=True,
            hide_col_field_labels=True,
            pane_cell_style={"font-size": "8"},
            axis_style={"title": ""},
        )
        sheet = metric + " Summary"
        editor.add_worksheet(sheet)
        editor.configure_layered_chart(
            sheet,
            rows=["YEAR(Order Date)"],
            panes=[
                {
                    "mark_type": "Text",
                    "label": "SUM(" + metric + ")",
                    "color": "YEAR(Order Date)",
                    "color_map": colors,
                    "detail_extra": ["Has Previous Year"],
                    "labels": [change],
                    "label_runs": [
                        {"field": "SUM(" + metric + ")", "fontsize": 16, "bold": True},
                        {"text": "\n"},
                        {"field": change, "fontsize": 12},
                    ],
                }
            ],
            filters=[
                {
                    "column": "YEAR(Order Date)",
                    "values": [2017, 2018, 2019],
                    "type": "categorical",
                },
                {"column": "Has Previous Year", "values": [True]},
            ],
            table_calc_overrides={
                change: [
                    {"ordering_type": "Field", "ordering_field": "YEAR(Order Date)"}
                ],
                "Has Previous Year": [
                    {"ordering_type": "Field", "ordering_field": "YEAR(Order Date)"}
                ],
            },
        )
        editor.configure_worksheet_style(
            sheet,
            hide_borders=True,
            hide_gridlines=True,
            hide_row_field_labels=True,
            cell_formats=[
                {"field": "YEAR(Order Date)", "height": "110"},
                {"width": "155"},
            ],
            header_formats=[{"field": "YEAR(Order Date)", "width": "30"}],
            label_formats=[
                {
                    "field": "YEAR(Order Date)",
                    "text-orientation": "-90",
                    "font-size": "9",
                }
            ],
            pane_cell_style={"text-align": "center"},
            table_formats=[{"attr": "width", "value": "160"}],
        )
    for sheet, metric, flag in [
        ("Top 10 Products by Sales", "Sales", "Show Top Sales"),
        ("Top & Bottom 10 Products by Profit", "Profit", "Show Extreme Profit"),
    ]:
        editor.add_worksheet(sheet)
        row_fields = (
            ["Product Name"]
            if metric == "Sales"
            else ["Top 10 Products by Profit", "Profit Group", "Product Name"]
        )
        editor.configure_layered_chart(
            sheet,
            columns=["SUM(" + metric + ")"],
            rows=row_fields,
            axis_shelf="columns",
            panes=[
                {
                    "axis": "SUM(" + metric + ")",
                    "mark_type": "Bar",
                    "label": "SUM(" + metric + ")",
                    "mark_style": {"mark-color": "#000000", "mark-labels-show": "true"},
                }
            ],
            sort_descending="SUM(" + metric + ")",
            sort_field="Product Name",
            filters=[
                {
                    "column": "YEAR(Order Date)",
                    "values": [2018, 2019],
                    "type": "categorical",
                    "context": True,
                },
                {"column": flag, "values": [True]},
            ],
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_borders=True,
            hide_row_field_labels=True,
            pane_cell_style={"font-size": "8"},
            cell_formats=[{"field": "Product Name", "width": "180"}],
            label_formats=(
                [
                    {"field": "Top 10 Products by Profit", "display": "false"},
                    {"field": "Profit Group", "text-orientation": "-90"},
                ]
                if metric == "Profit"
                else []
            ),
            axis_style={"title": ""},
        )
    layout = {
        "type": "vertical",
        "children": [
            {
                "type": "text",
                "text": "#WOW2020 WEEK21",
                "font_size": 20,
                "fixed_size": 50,
            }
        ],
    }
    for metric in ["Sales", "Profit"]:
        layout["children"].append(
            {
                "type": "text",
                "runs": [
                    {"text": metric.upper(), "font_size": 16, "font_alignment": "0"}
                ],
                "fixed_size": 34,
            }
        )
        products = (
            "Top 10 Products by Sales"
            if metric == "Sales"
            else "Top & Bottom 10 Products by Profit"
        )
        layout["children"].append(
            {
                "type": "horizontal",
                "children": [
                    {
                        "type": "worksheet",
                        "name": metric + " Summary",
                        "show_title": False,
                        "fixed_size": 200,
                        "fit": "entire",
                    },
                    {
                        "type": "worksheet",
                        "name": metric + " Line",
                        "show_title": False,
                        "weight": 4,
                        "fit": "entire",
                    },
                    {
                        "type": "worksheet",
                        "name": products,
                        "fixed_size": 550,
                        "fit": "entire",
                    },
                ],
            }
        )
    layout["children"].append(
        {
            "type": "text",
            "text": "DESIGNED BY LORNA BROWN | #WOW2020 WEEK 21 | RECREATED WITH CWTWB",
            "font_size": 8,
            "fixed_size": 40,
        }
    )
    editor.add_dashboard(
        DASHBOARD, width=1200, height=800, worksheet_names=SHEETS, layout=layout
    )
    editor.enable_automatic_phone_layout(DASHBOARD, worksheet_height=280)
    editor.set_active_dashboard(DASHBOARD)
    target = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    editor.save(target, validate=False)
    return target


if __name__ == "__main__":
    print(build())
