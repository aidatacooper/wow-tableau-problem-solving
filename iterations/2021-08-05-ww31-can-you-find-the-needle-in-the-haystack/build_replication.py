"""Rebuild the WW31 "needle in the haystack" dashboard.

The challenge (Candra McRae, built by Donna Coles) asks for a single filter
field that keeps the products that are simultaneously in the top 50 by sales,
unprofitable, and below the dataset's average number of distinct customers per
product. The answer is 13 products.

Chain:
  data (Product Name, Sub-Category, Category, Customer ID, Sales, Profit)
  → Customer Count Per Product = {FIXED [Product Name] : COUNTD([Customer ID])}
  → Count Products             = {FIXED : COUNTD([Product Name])}
  → Avg Overall Customer Count = {FIXED : SUM([Customer Count Per Product])}
                                 / [Count Products]
  → Higher than Avg Customer Count
        = AVG([Customer Count Per Product]) > SUM([Avg Overall Customer Count])
  → set "Top 50 Sales by Product"  (top 50 Product Name by SUM(Sales))
  → set "Unprofitable Products"    (Product Name whose SUM(Profit) < 0)
  → Products to Include = [Top 50 Sales by Product] AND [Unprofitable Products]
    (the single filter field the brief allows)
  → Chart: Product Name on Rows; a transparent MIN(1) bar column carrying the
    Product Name / Sub-Category | Category label, then a Sales bar column
    coloured by Higher than Avg Customer Count
  → dashboard 800x650 with the challenge footer

The author's "Products to Include" is a combined (intersection) set. cwtwb can
author set unions but not native set intersections, so the replica expresses the
same intersection as a boolean calculation over the two native sets. That is a
documented workaround: the sets stay dynamic and only one field filters the view.
"""

from pathlib import Path

from cwtwb import TWBEditor
from tableauhyperapi import Connection, HyperProcess, Telemetry

HERE = Path(__file__).resolve().parent
HYPER = next((HERE / "inputs").glob("*.hyper"))
DASHBOARD = "2021_08_04_WW31_Unprofitable_High_Sales"

# Author palette: true (higher than average) is grey, false is orange.
AVERAGE_COLORS = {"true": "#c8d0d9", "false": "#f7c480"}
ACCENT = "#f7c480"
MUTED = "#898989"

CUSTOMER_COUNT = "{FIXED [Product Name] : COUNTD([Customer ID])}"
COUNT_PRODUCTS = "{FIXED : COUNTD([Product Name])}"
AVG_OVERALL = "{FIXED: SUM([Customer Count Per Product])} / [Count Products]"
ABOVE_AVERAGE = "AVG([Customer Count Per Product]) > SUM([Avg Overall Customer Count])"
PROFIT_RATIO = "SUM([Profit])/SUM([Sales])"


def unprofitable_products():
    """Return the products whose total profit is negative, from the extract."""
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper,
        Connection(hyper.endpoint, str(HYPER)) as connection,
    ):
        rows = connection.execute_list_query(
            'SELECT "Product Name", SUM("Profit") FROM "Extract"."Extract" '
            'GROUP BY "Product Name"'
        )
    return sorted(name for name, profit in rows if profit < 0)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    # Author display format for sales labels and the Sales tooltip value.
    editor.set_field_format("Sales", 'c"$"#,##0,K')
    editor.set_field_format("Profit", 'c"$"#,##0,K;("$"#,##0,K)')

    # --- Customer-count measures -------------------------------------------
    editor.add_calculated_field(
        "Customer Count Per Product",
        CUSTOMER_COUNT,
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Count Products",
        COUNT_PRODUCTS,
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Avg Overall Customer Count",
        AVG_OVERALL,
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Higher than Avg Customer Count",
        ABOVE_AVERAGE,
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "MIN(1)",
        "MIN(1)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Profit Ratio",
        PROFIT_RATIO,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )

    # --- Native sets --------------------------------------------------------
    editor.add_set(
        "Top 50 Sales by Product",
        "Product Name",
        basis_field="Sales",
        aggregation="Sum",
        top_n=50,
        direction="DESC",
    )
    members = unprofitable_products()
    editor.add_set("Unprofitable Products", "Product Name", members=members)

    # Intersection expressed as one boolean field: the only filter in the view.
    editor.add_calculated_field(
        "Products to Include",
        "[Top 50 Sales by Product] AND [Unprofitable Products]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # --- Chart --------------------------------------------------------------
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["MIN(1)", "SUM(Sales)"],
        rows=["Product Name"],
        axis_shelf="columns",
        fold_axes=False,
        synchronized=False,
        sort_descending="SUM(Sales)",
        sort_field="Product Name",
        filters=[{"column": "Products to Include", "values": [True]}],
        panes=[
            {
                "axis": "MIN(1)",
                "mark_type": "Bar",
                "label": "Product Name",
                "labels": ["Sub-Category", "Category"],
                "label_runs": [
                    {"field": "Product Name", "fontsize": 9, "fontcolor": "#000000"},
                    {"text": "\n"},
                    {
                        "field": "Sub-Category",
                        "fontsize": 9,
                        "fontcolor": MUTED,
                        "prefix": "",
                    },
                    {"text": " | ", "fontsize": 9, "fontcolor": MUTED},
                    {"field": "Category", "fontsize": 9, "fontcolor": MUTED},
                ],
                "tooltip": [],
                "mark_sizing_off": True,
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "mark-transparency": "0",
                    "has-stroke": "false",
                    "size": "0.0099999997764825821",
                },
            },
            {
                "axis": "SUM(Sales)",
                "mark_type": "Bar",
                "color": "Higher than Avg Customer Count",
                "color_map": AVERAGE_COLORS,
                "label": "SUM(Sales)",
                "tooltip": [
                    "SUM(Profit)",
                    "Profit Ratio",
                    "SUM(Customer Count Per Product)",
                ],
                "mark_sizing_off": True,
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "true",
                    "size": "1.3293370008468628",
                },
            },
        ],
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_row_label="Product Name",
        hide_sort_controls=True,
        pane_cell_style={"vertical-align": "center"},
        panes_style=[
            {
                "cell_style": {"text-align": "left", "vertical-align": "center"},
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "true"},
            },
            {"cell_style": {"text-align": "left", "vertical-align": "center"}},
        ],
        cell_formats=[{"field": "Product Name", "height": 51}],
        pane_datalabel_style={"font-size": "9", "color": "#000000"},
        axis_style={
            "encodings": [
                {
                    "field": "MIN(1)",
                    "scope": "cols",
                    "class": "0",
                    "range-type": "fixed",
                    "min": "0",
                    "max": "2",
                }
            ],
            "per_field": [
                {"field": "MIN(1)", "scope": "cols", "attr": "display", "value": "false"},
                {"field": "SUM(Sales)", "scope": "cols", "attr": "display", "value": "false"},
            ],
        },
    )
    editor.configure_custom_tooltip(
        "Chart",
        [
            {"field": "Product Name", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"text": "\n\n"},
            {"text": "Sales:\t", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"field": "SUM(Sales)", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"text": "\n"},
            {"text": "Profit:\t", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"field": "SUM(Profit)", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"text": "\n"},
            {"text": "Profit Ratio:\t", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"field": "Profit Ratio", "bold": True, "fontcolor": "#666666", "fontsize": 9},
            {"text": "\n\n"},
            {
                "text": "# of Distinct Customers:\t",
                "bold": True,
                "fontcolor": "#666666",
                "fontsize": 9,
            },
            {
                "field": "SUM(Customer Count Per Product)",
                "bold": True,
                "fontcolor": "#666666",
                "fontsize": 9,
            },
        ],
        pane_index=1,
    )
    editor.set_worksheet_rich_title(
        "Chart",
        [
            {
                "text": "Can you Figure Out Which Unprofitable, High Sales Products to Focus On?",
                "bold": True,
                "fontsize": 12,
                "fontcolor": "#000000",
            },
            {"text": "\u00c6\n"},
            {"text": "Higher", "bold": True, "fontsize": 9, "fontcolor": "#b4b4b4"},
            {"text": " | ", "bold": True, "fontsize": 9, "fontcolor": "#000000"},
            {"text": "Lower", "bold": True, "fontsize": 9, "fontcolor": ACCENT},
            {"text": " Average Number of Customers", "fontsize": 9, "fontcolor": MUTED},
        ],
    )

    # --- Dashboard ----------------------------------------------------------
    def pos(x, y, w, h):
        return {
            "x": round(x / 800 * 100000),
            "y": round(y / 650 * 100000),
            "w": round(w / 800 * 100000),
            "h": round(h / 650 * 100000),
        }

    children = [
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": True,
            "fit": "entire",
            "absolute": pos(8, 8, 784, 578),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "CHALLENGE BY : CANDRA MCRAE",
                    "bold": True,
                    "font_size": 8,
                    "font_color": ACCENT,
                }
            ],
            "absolute": pos(8, 590, 261, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021  |  WEEK 31",
                    "bold": True,
                    "font_size": 8,
                    "font_color": ACCENT,
                }
            ],
            "absolute": pos(269, 590, 261, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "RECREATED WITH cwtwb",
                    "bold": True,
                    "font_size": 8,
                    "font_color": ACCENT,
                }
            ],
            "absolute": pos(531, 590, 261, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "http://www.workout-wednesday.com/2021w31tab/",
                    "font_size": 8,
                }
            ],
            "absolute": pos(8, 622, 784, 22),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=800,
        height=650,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["Chart"],
    )
    editor.set_window_state("Chart", hidden=False, zoom_entire_view=True)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
