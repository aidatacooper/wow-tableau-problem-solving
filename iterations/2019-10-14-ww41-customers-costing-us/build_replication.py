"""Build WW41 customer profitability diagnosis from locked Hyper."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from cwtwb.twb_editor import TWBEditor
from lxml import etree

HYPER = next((HERE / "inputs").glob("*.hyper"))
OUT = HERE / "outputs"


def build(p):
    e = TWBEditor("")
    e.set_hyper_connection(str(HYPER), table_name="Extract")
    e.add_calculated_field(
        "Profit Ratio",
        "SUM([Profit])/SUM([Sales])",
        datatype="real",
        default_format="p0%",
    )
    e.add_calculated_field(
        "Full Retail Price",
        "[Sales]/(1-[Discount])",
        datatype="real",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    e.add_calculated_field(
        "Lost Sales",
        "SUM([Full Retail Price])-SUM([Sales])",
        datatype="real",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    e.add_calculated_field(
        "Weighted Discount",
        "[Lost Sales]/SUM([Full Retail Price])",
        datatype="real",
        default_format="p0%",
    )
    e.add_calculated_field(
        "Total Customer Sales",
        "{ FIXED [Customer Name] : SUM([Sales]) }",
        datatype="real",
    )
    e.add_set("Selected Customer", "Customer Name")
    e.add_calculated_field(
        "Selected Customer Flag",
        "[Selected Customer]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Show Selected Customer",
        "IF { FIXED : MAX(INT([Selected Customer])) } = 0 THEN TRUE ELSE [Selected Customer] END",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Sales > 500",
        "[Total Customer Sales] > 500",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Label Customer",
        "IF [Sales > 500] THEN [Customer Name] END",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_worksheet("Scatter")
    e.configure_chart(
        "Scatter",
        mark_type="Circle",
        columns=["Weighted Discount"],
        rows=["Profit Ratio"],
        detail="Customer Name",
        size="MIN(Total Customer Sales)",
        color="Selected Customer",
        filters=[{"column": "Sales > 500", "values": ["true"]}],
        tooltip=["Customer Name", "Profit Ratio", "Weighted Discount", "Lost Sales"],
        color_map={"In": "#499894", "Out": "#a2a2a2"},
    )
    e.add_worksheet("Table")
    e.configure_chart(
        "Table",
        mark_type="Text",
        columns=["Measure Names"],
        rows=["Customer Name"],
        measure_values=[
            "SUM(Sales)",
            "SUM(Full Retail Price)",
            "Lost Sales",
            "Weighted Discount",
            "Profit Ratio",
        ],
        filters=[
            {"column": "Sales > 500", "values": ["true"]},
            {"column": "Show Selected Customer", "values": ["true"]},
        ],
        sort_descending="Lost Sales",
    )
    table_view = e._find_worksheet("Table").find("table/view")
    ds_name = e._datasource.get("name", "")
    measure_names = f"[{ds_name}].[:Measure Names]"
    measure_sort = etree.Element(
        "manual-sort", column=measure_names, direction="ASC"
    )
    dictionary = etree.SubElement(measure_sort, "dictionary")
    for expression in (
        "SUM(Sales)",
        "SUM(Full Retail Price)",
        "Lost Sales",
        "Weighted Discount",
        "Profit Ratio",
    ):
        ci = e.field_registry.parse_expression(expression)
        etree.SubElement(
            dictionary, "bucket"
        ).text = f'"{e.field_registry.resolve_full_reference(ci.instance_name)}"'
    shelf_sorts = table_view.find("shelf-sorts")
    aggregation = table_view.find("aggregation")
    if shelf_sorts is not None:
        shelf_sorts.addprevious(measure_sort)
    elif aggregation is not None:
        aggregation.addprevious(measure_sort)
    else:
        table_view.append(measure_sort)
    e.configure_worksheet_style(
        "Scatter",
        hide_table_dividers=True,
        pane_mark_style={
            "mark-labels-show": "false",
            "mark-color": "#a2a2a2",
            "mark-transparency": "129",
            "has-stroke": "true",
            "stroke-color": "#666666",
        },
    )
    e.configure_worksheet_style(
        "Table",
        hide_table_dividers=True,
        header_formats=[{"font-family": "Tableau Book", "height": "52"}],
    )
    e.add_dashboard(
        "WW41 Customers Costing Us",
        width=1100,
        height=600,
        layout={
            "type": "container",
            "direction": "vertical",
            "children": [
                {
                    "type": "text",
                    "text": "WEEK 41 : WHICH CUSTOMERS ARE COSTING US?",
                    "font_size": "14",
                    "bold": True,
                    "color": "#499894",
                    "fixed_size": 42,
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        {
                            "type": "container",
                            "direction": "vertical",
                            "children": [
                                {
                                    "type": "worksheet",
                                    "name": "Scatter",
                                    "show_title": False,
                                    "weight": 1,
                                },
                                {
                                    "type": "text",
                                    "text": "Each dot represents a customer with at least\n$500 lifetime sales.\nSelect customer(s) to view in table to the right.",
                                    "color": "#777777",
                                    "fixed_size": 82,
                                },
                            ],
                        },
                        {
                            "type": "worksheet",
                            "name": "Table",
                            "show_title": False,
                            "weight": 1,
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": "DESIGNED BY : LUKE STANKE                         #WORKOUTWEDNESDAY  |  2019  |  WEEK 41                         RECREATED BY: DONNA COLES",
                    "font_size": "8",
                    "color": "#499894",
                    "fixed_size": 28,
                },
            ],
        },
        worksheet_names=["Scatter", "Table"],
    )
    e.add_dashboard_set_action(
        "WW41 Customers Costing Us",
        "Scatter",
        "Selected Customer",
        event_type="on-select",
        caption="Select Customer",
        clear_option="exclude-all",
    )
    OUT.mkdir(exist_ok=True)
    e.save(p, validate=False)
    return p


if __name__ == "__main__":
    for n in (
        "2019-10-14-ww41-customers-costing-us-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUT / n))
