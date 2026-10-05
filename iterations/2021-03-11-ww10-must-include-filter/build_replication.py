"""Build the "must include" two-stage product filter from locked Superstore data.

The business question: which orders contain a first chosen product, and of those
which also contain a second required product, then report the resulting orders,
their order-level totals and the aggregate BANs.

The behaviour is reproduced with two sets over PRODUCT, two
``{FIXED [ORDER ID]: MAX(...)}`` order-level flags, a context filter on the first
flag and an ordinary filter on the second, plus an order-detail worksheet exposed
as a Viz in Tooltip.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_03_10_WW10_Must_Include_Filter"
CURRENCY = 'c"$"#,##0;("$"#,##0)'
PERCENT = "p0.0%"
NUMBER = "n#,##0;-#,##0"
HYPER = HERE / "inputs/Orders (Sample - Superstore).hyper"


def zone(kind, x, y, width, height, **options):
    """Floating dashboard zone helper using absolute 1/100000 coordinates."""
    return {
        "type": kind,
        "absolute": {"x": x, "y": y, "w": width, "h": height},
        "style": {
            "background-color": "#ffffff",
            "margin": 0,
            "border-style": "none",
            "border-width": 0,
        },
        **options,
    }


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Sets over PRODUCT -------------------------------------------------
    # The author sets use Tableau's "Use All" condition, so the default state
    # keeps every order.
    editor.add_set("1st Products", "Product Name", use_all=True)
    editor.add_set("2nd Product", "Product Name", use_all=True)

    # --- Order-level "must include" flags ----------------------------------
    for name, set_name in (
        ("Order has 1st Products", "1st Products"),
        ("Order has 2nd Product", "2nd Product"),
    ):
        editor.add_calculated_field(
            name,
            f"{{FIXED [Order ID]: MAX([{set_name}])}}",
            datatype="boolean",
            role="dimension",
            field_type="nominal",
        )

    # --- Order-detail helper ----------------------------------------------
    editor.add_calculated_field(
        "QTY",
        "[Quantity]",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        default_format=NUMBER,
    )

    # --- BAN measures ------------------------------------------------------
    editor.add_calculated_field(
        "# ORDERS",
        "COUNTD([Order ID])",
        datatype="integer",
        role="measure",
        default_format=NUMBER,
    )
    editor.add_calculated_field(
        "Total Orders", "{FIXED:COUNTD([Order ID])}", datatype="integer", role="measure"
    )
    editor.add_calculated_field(
        "% OF TOTAL ORDERS",
        "[# ORDERS]/SUM([Total Orders])",
        datatype="real",
        role="measure",
        default_format=PERCENT,
    )
    editor.add_calculated_field(
        "AVG ORDER AMOUNT",
        "SUM([Sales]) / [# ORDERS]",
        datatype="real",
        role="measure",
        default_format=CURRENCY,
    )
    editor.add_calculated_field(
        "AVG ORDER QUANTITY",
        "SUM([Quantity])/[# ORDERS]",
        datatype="real",
        role="measure",
        default_format=NUMBER,
    )
    editor.set_field_format("Sales", CURRENCY)

    # --- Order-level filters ------------------------------------------------
    # Stage 1 is a context filter on Bars/Order Detail so stage 2 evaluates
    # inside the already-qualifying orders. BANs deliberately keeps stage 1 out
    # of context: a context filter would scope {FIXED:COUNTD([Order ID])} to the
    # qualifying orders and break the "% of total orders" denominator.
    must_include_first = {
        "column": "Order has 1st Products",
        "values": ["true"],
        "context": True,
    }
    must_include_first_plain = {
        "column": "Order has 1st Products",
        "values": ["true"],
    }
    must_include_second = {"column": "Order has 2nd Product", "values": ["true"]}

    # --- Bars: order-level Sales and Quantity -------------------------------
    # The author places the two measures directly on the columns shelf, which
    # gives the two side-by-side numeric axes. (configure_chart's measure_values
    # path is not used: it emits a Measure Values encoding that renders an empty
    # view on this datasource — see analysis.md.)
    editor.add_worksheet("Bars")
    editor.configure_chart(
        "Bars",
        mark_type="Bar",
        rows=["Order ID", "Customer Name"],
        columns=["SUM(Sales)", "SUM(Quantity)"],
        sort_descending="SUM(Sales)",
        sort_field="Order ID",
        filters=[must_include_first, must_include_second],
    )
    editor.configure_worksheet_style(
        "Bars",
        hide_gridlines=True,
        hide_table_dividers=True,
        header_formats=[
            {"field": "Order ID", "font-size": 8},
            {"field": "Customer Name", "font-size": 8, "width": "132"},
        ],
        cell_formats=[{"field": "Customer Name", "height": "26"}],
    )

    # --- Order Detail: line items for the hovered order --------------------
    editor.add_worksheet("Order Detail")
    editor.configure_layered_chart(
        "Order Detail",
        rows=["Customer Name", "Order ID", "Product Name"],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "labels": ["Measure Names"],
                "measure_values": ["SUM(Sales)", "SUM(QTY)"],
            }
        ],
        filters=[must_include_first, must_include_second],
    )
    editor.configure_subtotals(
        "Order Detail",
        measure_fields=["SUM(Sales)", "SUM(QTY)"],
        aggregation="Sum",
        subtotal_fields=["Order ID"],
        label="Grand Total",
    )
    editor.configure_worksheet_style(
        "Order Detail",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
        label_formats=[
            {"field": "Customer Name", "display": False},
            {"field": "Order ID", "display": False},
        ],
    )

    editor.configure_custom_tooltip(
        "Bars",
        [
            {"field": "Order ID", "bold": True},
            {"text": " | "},
            {"field": "Customer Name", "bold": True},
            {"text": "\nSales: "},
            {"field": "SUM(Sales)", "bold": True, "fontsize": 8},
            {"text": "\nQuantity: "},
            {"field": "SUM(Quantity)", "bold": True, "fontsize": 8},
            {"text": "\n\nORDER DETAILS\n"},
            {
                "sheet": {
                    "name": "Order Detail",
                    "filter_fields": ["Customer Name", "Order ID"],
                    "maxwidth": 300,
                    "maxheight": 300,
                }
            },
        ],
        pane_index=0,
    )

    # --- BANs ---------------------------------------------------------------
    editor.add_worksheet("BANs")
    editor.configure_layered_chart(
        "BANs",
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "labels": ["Measure Names"],
                "measure_values": [
                    "# ORDERS",
                    "% OF TOTAL ORDERS",
                    "AVG ORDER AMOUNT",
                    "AVG ORDER QUANTITY",
                ],
            }
        ],
        filters=[must_include_first_plain, must_include_second],
    )
    editor.configure_worksheet_style(
        "BANs",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_borders=True,
        table_formats=[
            {"attr": "stroke-size", "scope": "rows", "value": "3"},
            {"attr": "stroke-color", "scope": "rows", "value": "#c4c4c4"},
        ],
    )

    # --- Dashboard ---------------------------------------------------------
    children = [
        zone(
            "text",
            667,
            889,
            63750,
            7112,
            runs=[
                {
                    "text": 'CAN YOU BUILD A "MUST INCLUDE" FILTER?',
                    "bold": True,
                    "font_size": 16,
                    "font_alignment": "0",
                    "font_color": "#333333",
                }
            ],
        ),
        zone(
            "worksheet",
            667,
            8001,
            98666,
            15254,
            name="BANs",
            show_title=False,
            fit="entire",
        ),
        zone(
            "worksheet",
            667,
            23255,
            98666,
            68745,
            name="Bars",
            show_title=False,
            fit="width",
        ),
        zone(
            "text",
            667,
            92000,
            32888,
            3556,
            runs=[
                {
                    "text": "CHALLENGE BY : ANN JACKSON",
                    "bold": True,
                    "font_size": 8,
                    "font_color": "#31a1b3",
                    "font_alignment": "0",
                }
            ],
        ),
        zone(
            "text",
            33555,
            92000,
            32890,
            3556,
            runs=[
                {
                    "text": "#WOW2021  |  WEEK 10",
                    "bold": True,
                    "font_size": 8,
                    "font_color": "#31a1b3",
                    "font_alignment": "1",
                }
            ],
        ),
        zone(
            "text",
            66445,
            92000,
            32888,
            3556,
            runs=[
                {
                    "text": "RECREATED WITH CWTWB",
                    "bold": True,
                    "font_size": 8,
                    "font_color": "#31a1b3",
                    "font_alignment": "2",
                }
            ],
        ),
        zone(
            "text",
            667,
            95556,
            98666,
            3555,
            runs=[
                {
                    "text": "http://www.workout-wednesday.com/2021w10tab/",
                    "font_size": 8,
                    "font_alignment": "1",
                }
            ],
        ),
    ]

    # Native set controls bound to the two PRODUCT sets.
    children.append(
        zone(
            "set_control",
            64417,
            889,
            18500,
            7112,
            worksheet="Bars",
            field="1st Products",
            caption="SELECT PRODUCTS",
            mode="checkdropdown",
            show_apply=True,
        )
    )
    children.append(
        zone(
            "set_control",
            82917,
            889,
            16416,
            7112,
            worksheet="Bars",
            field="2nd Product",
            caption="ORDER MUST ALSO INCLUDE",
            mode="dropdown",
        )
    )

    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=900,
        layout={"type": "container", "direction": "floating", "children": children},
    )
    # Order Detail is a viz-in-tooltip source: it must stay off the dashboard
    # viewpoint list, exactly like the author workbook.
    for name in ("Bars", "BANs"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)
        editor.set_worksheet_title(name, "")
    editor.set_window_state("Order Detail", hidden=True)
    editor.set_worksheet_title("Order Detail", "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
