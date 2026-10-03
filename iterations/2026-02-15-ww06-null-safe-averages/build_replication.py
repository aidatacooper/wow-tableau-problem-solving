"""Build WW06 from independent Hyper with public cwtwb APIs only."""

from pathlib import Path
from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs/Sample - Superstore_Orders.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"
DASHBOARD = "2026_02_11_WW06_Averages_and_Nulls"


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    editor.set_date_options(start_of_week="sunday")
    for parameter, date in [("pMinDate", "2025-07-11"), ("pMaxDate", "2025-07-23")]:
        editor.add_parameter(
            parameter, datatype="date", default_value=f"#{date}#", domain_type="any"
        )
    for name, formula, datatype, role, field_type in [
        ("#Orders", "COUNTD([Order ID])", "integer", "measure", "quantitative"),
        (
            "#Orders in Date Range",
            "ZN(COUNTD(IF [Order Date] >= [pMinDate] AND [Order Date] <= [pMaxDate] THEN [Order ID] END))",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Number Prefix *",
            "IIF([#Orders in Date Range]=0,'*',NULL)",
            "string",
            "measure",
            "nominal",
        ),
        ("Min Date", "MIN([Order Date])", "date", "measure", "ordinal"),
        ("Max Date", "MAX([Order Date])", "date", "measure", "ordinal"),
        (
            "Colour",
            "[Min Date] = [pMinDate] AND [Max Date] = [pMaxDate]",
            "boolean",
            "measure",
            "nominal",
        ),
        (
            "Tooltip - 0 orders",
            "IIF([Number Prefix *]='*','* No orders found for this period',NULL)",
            "string",
            "measure",
            "nominal",
        ),
        ("True", "TRUE", "boolean", "dimension", "nominal"),
        ("False", "FALSE", "boolean", "dimension", "nominal"),
        ("Apply Text", "'Apply'", "string", "dimension", "nominal"),
    ]:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format="n#,##0;-#,##0" if datatype == "integer" else "",
        )
    editor.add_calculated_field(
        "Index", "INDEX()", datatype="integer", table_calc="Rows"
    )
    editor.add_hierarchy(
        "Category Hierarchy", ["Category", "Sub-Category", "Manufacturer"]
    )
    editor.add_worksheet("Viz")
    editor.configure_chart(
        "Viz",
        mark_type="Square",
        columns=["WEEKDAY(Order Date)"],
        rows=["Category", "Sub-Category"],
        color="#Orders in Date Range",
        label="#Orders in Date Range",
        label_extra=["Number Prefix *"],
        tooltip=["#Orders", "Tooltip - 0 orders"],
        label_runs=[{"field": "Number Prefix *"}, {"field": "#Orders in Date Range"}],
        filters=[
            {
                "column": "Category",
                "values": ["Furniture", "Office Supplies", "Technology"],
            }
        ],
    )
    editor.enable_domain_completion("Viz", field_name="Index")
    editor.configure_subtotals(
        "Viz",
        measure_fields=["#Orders", "#Orders in Date Range"],
        aggregation="Average",
        subtotal_fields=["Category", "Sub-Category"],
        label="Avg.",
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_table_dividers=True,
        hide_col_field_labels=True,
        pane_formats=[
            {"border_width": 1, "border_style": "solid", "border_color": "#898989"},
            {
                "data_class": "subtotal",
                "background_color": "#00000000",
                "border_color": "#f28e2b",
                "border_width": 2,
            },
        ],
        header_formats=[
            {"field": "Sub-Category", "width": 124},
            {"field": "Category", "width": 84},
            {"border_color": "#898989", "border_style": "solid"},
            {
                "background_color": "#f6eee3",
                "border_color": "#f28e2b",
                "border_width": 2,
                "data_class": "subtotal",
            },
        ],
        label_formats=[
            {"field": "WEEKDAY(Order Date)", "text-format": "iEEE"},
            {
                "field": "Sub-Category",
                "font-family": "Tableau Medium",
                "font-weight": "normal",
                "color": "#000000",
            },
            {"field": "Category", "color": "#000000"},
        ],
        color_style={
            "field": "#Orders in Date Range",
            "palette": "red_blue_white_diverging_10_0",
            "center": 0.0,
            "include_totals": True,
        },
        cell_formats=[
            {"field": "WEEKDAY(Order Date)", "width": 114},
            {"field": "Sub-Category", "height": 25},
            {"border-color": "#898989", "border-style": "solid"},
            {
                "field": "#Orders in Date Range",
                "text-format": "n#,##0.00;-#,##0.00",
                "data-class": "subtotal",
            },
            {
                "field": "#Orders in Date Range",
                "font-weight": "bold",
                "data-class": "subtotal",
            },
        ],
        pane_mark_style={
            "has_stroke": "true",
            "stroke_color": "#666666",
            "size": "14.547999382019043",
        },
    )
    editor.add_worksheet("Apply Button Filter")
    editor.configure_chart(
        "Apply Button Filter",
        mark_type="Square",
        label="Apply Text",
        detail="AGG(Max Date)",
        tooltip=["AGG(Min Date)", "True", "False"],
        color="Colour",
        filters=[
            {
                "column": "Order Date",
                "type": "quantitative",
                "min": "#2025-07-11#",
                "max": "#2025-07-23#",
                "context": True,
            }
        ],
        color_map={"true": "#D9D9D9", "false": "#F28E2B"},
    )
    editor.configure_worksheet_style(
        "Apply Button Filter",
        hide_axes=True,
        hide_gridlines=True,
        hide_borders=True,
        disable_tooltip=True,
        pane_mark_style={"size": "14.547999382019043", "mark-labels-show": "true"},
    )
    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"background-color": "#f5f5f5"},
        "children": [
            {
                "type": "text",
                "text": "#WOW2026  |  WEEK 6  |  Can you account for nulls in your average?",
                "runs": [
                    {
                        "text": "#WOW2026  |  WEEK 6  |  Can you account for nulls in your average?",
                        "font_size": "12",
                        "font_alignment": "0",
                        "font_color": "#333333",
                    }
                ],
                "style": {"background-color": "#ffffff", "padding": 5},
                "absolute": {"x": 0, "y": 0, "w": 100000, "h": 5469},
            },
            {
                "type": "text",
                "text": "Superstore Order Status by Day of Week",
                "runs": [
                    {
                        "text": "Superstore Order Status by Day of Week",
                        "font_size": "15",
                        "font_alignment": "0",
                        "font_color": "#1b1b1b",
                    }
                ],
                "style": {"margin": 10},
                "absolute": {"x": 0, "y": 5469, "w": 100000, "h": 7161},
            },
            {
                "type": "empty",
                "style": {"background-color": "#ffffff"},
                "absolute": {"x": 21816, "y": 12630, "w": 78184, "h": 84635},
            },
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "width",
                "style": {"background-color": "#ffffff", "padding": 30},
                "absolute": {"x": 21816, "y": 12630, "w": 78184, "h": 84635},
            },
            {
                "type": "filter",
                "worksheet": "Apply Button Filter",
                "field": "Order Date",
                "caption": "Order Date",
                "mode": "range",
                "style": {"margin": 10, "background-color": "#f5f5f5"},
                "absolute": {"x": 1464, "y": 15234, "w": 18888, "h": 11719},
            },
            {
                "type": "worksheet",
                "name": "Apply Button Filter",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 14788, "y": 28255, "w": 4832, "h": 3776},
            },
            {
                "type": "filter",
                "worksheet": "Viz",
                "field": "Category",
                "mode": "checklist",
                "show_apply": True,
                "style": {"margin": 10, "background-color": "#f5f5f5"},
                "absolute": {"x": 1464, "y": 33333, "w": 18888, "h": 21875},
            },
            {
                "type": "text",
                "text": "CHALLENGE BY: Yusuke Nakanishi\nRECREATED BY: Donna Coles\n#WOW2026  |  WEEK 6",
                "runs": [
                    {
                        "text": "CHALLENGE BY: Yusuke Nakanishi\nRECREATED BY: Donna Coles\n#WOW2026  |  WEEK 6",
                        "font_size": "8",
                        "font_alignment": "0",
                        "font_color": "#666666",
                    }
                ],
                "absolute": {"x": 1464, "y": 85156, "w": 18888, "h": 8073},
            },
            {
                "type": "text",
                "text": "* No orders for this period",
                "runs": [
                    {
                        "text": "* No orders for this period",
                        "font_size": "8",
                        "font_alignment": "2",
                        "font_color": "#333333",
                    }
                ],
                "absolute": {"x": 85871, "y": 12630, "w": 13909, "h": 3906},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1366,
        height=768,
        layout=layout,
        worksheet_names=["Viz", "Apply Button Filter"],
    )
    for source, target, date in [
        ("Min Date", "pMinDate", "2025-07-11"),
        ("Max Date", "pMaxDate", "2025-07-23"),
    ]:
        editor.add_dashboard_action(
            DASHBOARD,
            action_type="parameter",
            source_sheet="Apply Button Filter",
            source_field=source,
            target_parameter=target,
            aggregation="attr",
            clear_value=f"d:{date}",
            caption=f"Set {source}",
        )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Apply Button Filter",
        target_sheet="Apply Button Filter",
        field_mappings={"False": "True"},
        caption="Deselect Button",
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2026-02-15-ww06-null-safe-averages-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
