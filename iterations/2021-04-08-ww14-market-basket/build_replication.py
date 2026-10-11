"""Rebuild the WW14 market-basket "profitable return customer bundles" dashboard.

The challenge asks, for a customer's *second* order, which other Sub-Categories
were bought alongside a chosen Sub-Category, and whether each of those was
profitable. Two sheets share the answer: a horizontal bar chart and a treemap,
ordered by order count, toggled by a parameter action.

The article's chain:

- ``Is Customer's First Order? = {FIXED [Customer ID]: MIN([Order Date])} =
  [Order Date]``; a data-source filter keeps only ``False`` so the customer's
  first order drops out of the domain.
- ``Is Customer's 2nd Order? = {FIXED [Customer ID]:
  MIN(IIF([Is Customer's First Order]=False, [Order Date], NULL))} = [Order Date]``
  — the article's own alternative to relying on extract-filter ordering, so the
  workbook is self-contained.
- ``Customer Ordered Selected SubCat = IIF([pSelected_SubCat]=[Sub-Category],1,0)``
  and ``Orders with Selected SubCat`` = the orders where that sums to at least
  one (the article offers a Set or the LoD
  ``{FIXED [Order ID]: SUM(...)} >= 1``; the LoD route is used here because it
  needs no condition-based Set object).
- ``Other Items Ordered = IF [pSelected_SubCat]=[Sub-Category] THEN 'N/A' ELSE
  [Sub-Category] END``, filtered to exclude N/A.
- ``Profit Ratio = SUM([Profit])/SUM([Sales])`` and ``Is Profitable? =
  [Profit Ratio] > 0`` colour the marks.

The Toggle sheet is the article's native two-axis switch: ``MIN(0)`` and the
parameter-driven ``Selected Toggle`` share a synchronised column axis; a Circle
mark rides the parameter axis, and a parameter action on select sets ``Toggle``
from the clicked position. The Bar sheet shows only while ``Toggle = 0`` and the
Treemap only while ``Toggle = 1``.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_190looh0vamnc316c90ra0i8scth.hyper"
DASHBOARD = "2021_04_07_WW14_MarketBasketAnalysis"
SUBCATEGORIES = [
    "Accessories", "Appliances", "Art", "Binders", "Bookcases", "Chairs",
    "Copiers", "Envelopes", "Fasteners", "Furnishings", "Labels", "Machines",
    "Paper", "Phones", "Storage", "Supplies", "Tables",
]
# Author palette: profitable marks are neutral grey, unprofitable are orange.
PROFIT_COLORS = {"true": "#b3b7b8", "false": "#ee7c58"}


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Parameters ---------------------------------------------------------
    editor.add_parameter(
        "pSelected_SubCat",
        datatype="string",
        default_value="Accessories",
        domain_type="list",
        allowed_values=SUBCATEGORIES,
    )
    editor.add_parameter(
        "Toggle",
        datatype="integer",
        default_value="0",
        domain_type="list",
        allowed_values=["0", "1"],
    )

    # --- Customer's second order -------------------------------------------
    editor.add_calculated_field(
        "Is Customer's First Order",
        "{FIXED [Customer ID]: MIN([Order Date])} = [Order Date]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Is Customer's 2nd Order",
        "{FIXED [Customer ID]: MIN(IIF([Is Customer's First Order]=False,"
        " [Order Date], NULL))} = [Order Date]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # --- Orders containing the selected Sub-Category ------------------------
    editor.add_calculated_field(
        "Customer Ordered Selected SubCat",
        "IIF([pSelected_SubCat]=[Sub-Category],1,0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Orders with Selected SubCat",
        "{FIXED [Order ID]: SUM([Customer Ordered Selected SubCat])}>=1",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Other Items Ordered",
        "IF [pSelected_SubCat]=[Sub-Category] THEN 'N/A' ELSE [Sub-Category] END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )

    # --- Measures and profitability ----------------------------------------
    editor.add_calculated_field(
        "Count Orders",
        "COUNTD([Order ID])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Profit Ratio",
        "SUM([Profit])/SUM([Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )
    editor.add_calculated_field(
        "Is Profitable?",
        "[Profit Ratio]>0",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    # --- Toggle control -----------------------------------------------------
    editor.add_calculated_field(
        "Selected Toggle",
        "[Toggle]",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Toggle Label",
        "IF [Toggle]=0 THEN 'Bar' ELSE 'Treemap' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Colour",
        "IF [Toggle]=0 THEN 'grey' ELSE 'green' END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field("True", "True", datatype="boolean", role="dimension", field_type="nominal")
    editor.add_calculated_field("False", "False", datatype="boolean", role="dimension", field_type="nominal")
    editor.add_calculated_field("MIN0", "MIN(0)", datatype="integer", role="measure", field_type="quantitative")
    editor.add_calculated_field("MIN1", "MIN(1)", datatype="integer", role="measure", field_type="quantitative")

    tooltip = [
        "Count Orders",
        "Other Items Ordered",
        "SUM(Sales)",
        "SUM(Profit)",
        "Profit Ratio",
    ]
    base_filters = [
        {"column": "Is Customer's 2nd Order", "values": ["true"]},
        {"column": "Orders with Selected SubCat", "values": ["true"]},
        {"column": "Other Items Ordered", "values": ["N/A"], "kind": "hide", "exclude": True},
    ]

    # --- Bar chart ----------------------------------------------------------
    editor.add_worksheet("Bar")
    editor.configure_chart(
        "Bar",
        mark_type="Bar",
        rows=["Other Items Ordered"],
        columns=["Count Orders"],
        color="Is Profitable?",
        color_map=PROFIT_COLORS,
        label="Count Orders",
        tooltip=tooltip,
        sort_descending="Count Orders",
        sort_field="Other Items Ordered",
        filters=[
            *base_filters,
            {"column": "Selected Toggle", "type": "quantitative", "max": "0"},
        ],
    )
    editor.configure_custom_tooltip(
        "Bar",
        [
            {"text": "There were "},
            {"field": "Count Orders", "bold": True, "underline": True},
            {"text": " orders where the customer ordered "},
            {"text": "the selected Sub-Category", "bold": True},
            {"text": " and also placed an order for "},
            {"field": "Other Items Ordered", "bold": True},
            {"text": " on their second purchase with Superstore Inc.\n\nNet Sales :\t"},
            {"field": "SUM(Sales)", "bold": True},
            {"text": "\nProfit :\t"},
            {"field": "SUM(Profit)", "bold": True},
            {"text": "\nProfit Ratio :\t"},
            {"field": "Profit Ratio", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Bar",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_axes=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        label_formats=[{"field": "Other Items Ordered", "font-size": "11"}],
    )

    # --- Treemap ------------------------------------------------------------
    # A treemap has no shelf dimension: the Sub-Category sits on Detail, the
    # order count drives Size, and the same computed sort applies.
    editor.add_worksheet("Treemap")
    editor.configure_layered_chart(
        "Treemap",
        rows=[],
        columns=[],
        axis_shelf="cols",
        sort_mode="computed",
        sort_descending="Count Orders",
        sort_field="Other Items Ordered",
        panes=[
            {
                "mark_type": "Square",
                "size": "Count Orders",
                "color": "Is Profitable?",
                "color_map": PROFIT_COLORS,
                "label": "Count Orders",
                "labels": ["Other Items Ordered"],
                "detail": "Other Items Ordered",
                "tooltip": tooltip,
            }
        ],
        filters=[
            *base_filters,
            {"column": "Selected Toggle", "type": "quantitative", "min": "1"},
        ],
    )
    editor.configure_custom_tooltip(
        "Treemap",
        [
            {"text": "There were "},
            {"field": "Count Orders", "bold": True, "underline": True},
            {"text": " orders where the customer ordered "},
            {"text": "the selected Sub-Category", "bold": True},
            {"text": " and also placed an order for "},
            {"field": "Other Items Ordered", "bold": True},
            {"text": " on their second purchase with Superstore Inc.\n\nNet Sales :\t"},
            {"field": "SUM(Sales)", "bold": True},
            {"text": "\nProfit :\t"},
            {"field": "SUM(Profit)", "bold": True},
            {"text": "\nProfit Ratio :\t"},
            {"field": "Profit Ratio", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Treemap",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_axes=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
    )

    # --- Toggle control sheet ----------------------------------------------
    # MIN(0) and the parameter-driven Selected Toggle share a synchronised
    # column axis; the Circle mark rides the Selected Toggle axis.
    editor.add_worksheet("Toggle")
    editor.configure_layered_chart(
        "Toggle",
        columns=["Multiple Values", "Selected Toggle"],
        axis_shelf="cols",
        fold_axes=True,
        synchronized=True,
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Line",
                "measure_values": ["MIN0", "MIN1"],
                "color": "Colour",
                "size": "MIN0",
                "tooltip": [],
            },
            {
                "axis": "Selected Toggle",
                "mark_type": "Circle",
                "color": "Colour",
                "size": "Selected Toggle",
                "tooltip": ["Toggle Label"],
            },
        ],
        filters=[{"column": "Colour", "values": ["grey", "green"]}],
    )
    editor.configure_worksheet_style(
        "Toggle",
        background_color="#f5f5f5",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
    )

    # --- Dashboard ----------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "text",
                "runs": [
                    {"text": "Can you recommend profitable return customer product bundles?",
                     "bold": True, "font_size": "15", "font_color": "#333333"},
                    {"text": "\nOn a second purchase, when customers purchased "},
                    {"text": "the selected Sub-Category", "bold": True, "font_size": "12"},
                    {"text": ", what else did they buy?"},
                    {"text": "\nProfitable  |  "},
                    {"text": "Unprofitable", "font_color": "#ee7c58"},
                ],
                "absolute": {"x": 727, "y": 1000, "w": 83819, "h": 11500},
            },
            # Bar and Treemap stack in one flow container. The Toggle filter
            # leaves exactly one of them with data, and an empty worksheet
            # collapses to zero height in a flow container, so the visible sheet
            # fills the chart region (the author's sheet-swap behaviour).
            {
                "type": "container",
                "direction": "vertical",
                "absolute": {"x": 727, "y": 12500, "w": 83819, "h": 82500},
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Bar",
                        "show_title": False,
                        "fit": "entire",
                        "weight": 1,
                    },
                    {
                        "type": "worksheet",
                        "name": "Treemap",
                        "show_title": False,
                        "fit": "entire",
                        "weight": 1,
                    },
                ],
            },
            {
                "type": "worksheet",
                "name": "Toggle",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 84546, "y": 1000, "w": 14727, "h": 10125},
            },
            {
                "type": "paramctrl",
                "param": "pSelected_SubCat",
                "absolute": {"x": 84546, "y": 11125, "w": 14727, "h": 40000},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1100,
        height=800,
        layout=layout,
        worksheet_names=["Bar", "Treemap", "Toggle"],
    )

    # Selecting a point on the Toggle chart sets the Toggle parameter from the
    # clicked measure value (the article passes Measure Values into Toggle).
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Toggle",
        source_field="Measure Names",
        target_parameter="Toggle",
        aggregation="sum",
        clear_value="i:1",
        caption="Parameter1",
    )
    # Map True -> False so clicking never leaves a selection highlight behind.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Toggle",
        target_sheet="Toggle",
        field_mappings={"True": "False"},
        caption="Deselect Toggle",
    )

    for name in ("Bar", "Treemap", "Toggle"):
        editor.set_window_state(name, hidden=False)
        editor.set_worksheet_title(name, "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
