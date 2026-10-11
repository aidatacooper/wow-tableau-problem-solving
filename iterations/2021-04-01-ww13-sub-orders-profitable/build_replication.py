"""Rebuild the WW13 modified-mekko "profitable sub-orders" chart.

The challenge asks for a modified mekko (marimekko) chart on the Superstore
data at the Sub-Category/Order grain:

- bar height = the percentage of that Sub-Category's orders that are profitable
  (and, in the lower bar, one minus that percentage);
- bar width = the Sub-Category's share of total sales;
- bars ordered by percentage profitable, then by total sales.

A single order can contain product lines from several Sub-Categories, so an
order only counts as profitable for a Sub-Category when the *total* profit of
that Sub-Category's lines on the order is positive. That is a FIXED LoD
(``IIF({FIXED [Order ID],[Sub-Category]: SUM([Profit])}>0,1,0)``) — this
challenge does not forbid it.

The bars sit side by side along a cumulative-sales axis rather than on the
Sub-Category dimension, because each bar's width is data-driven. Two stacked
panes share the row axis: the upper pane plots ``Profitable Orders`` against a
normal axis and the lower pane plots ``Non Profitable Orders`` against a
reversed axis, so the pair straddles the zero line. ``% of Total Sales`` on the
Size shelf (fixed, right-aligned) gives the mekko widths, and a constant zero
reference line draws the black separator.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_0b8j5fu1vhrl6t1c1kh4511pxgj6.hyper"
DASHBOARD = "2021_03_31_WW13_Percentage_Sub_Orders_Profitable"

# Author palette: pink for the profitable share, warm grey for the rest.
MEASURE_NAMES_PALETTE = {
    "Profitable Orders": "#c290b4",
    "Non Profitable Orders": "#bab0ac",
}


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Order-grain profitability and the two percentages -----------------
    editor.add_calculated_field(
        "Order Is Profitable",
        "IIF({FIXED [Order ID],[Sub-Category]: SUM([Profit])}>0,1,0)",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Count Orders",
        "COUNTD([Order ID])",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Profitable Orders",
        "SUM([Order Is Profitable])/[Count Orders]",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )
    editor.add_calculated_field(
        "Non Profitable Orders",
        "1 - [Profitable Orders]",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )
    editor.add_calculated_field(
        "% of Total Sales",
        "SUM([Sales])/TOTAL(SUM([Sales]))",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )
    editor.add_calculated_field(
        "% Total Sales Cumulative",
        "RUNNING_SUM([% of Total Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
    )
    # A string sort key that keeps the intended order once the Sub-Category
    # dimension can no longer sit on a shelf (the bars are positioned by the
    # cumulative sales axis).
    editor.add_calculated_field(
        "Sort",
        'STR(ROUND([Profitable Orders],2)) + "-" + STR(ROUND(SUM([Sales])/1000000,2))',
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    # --- Viz: the mekko itself ---------------------------------------------
    # % of Total Sales totals over the whole table and the cumulative version
    # is addressed by Sub-Category, exactly as the article sets it.
    overrides = {
        "% of Total Sales": [{"ordering_type": "Rows"}],
        "% Total Sales Cumulative": [
            {"ordering_type": "Field", "ordering_field": "Sub-Category"},
        ],
    }

    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        rows=["Profitable Orders", "Non Profitable Orders"],
        columns=["% Total Sales Cumulative"],
        axis_shelf="rows",
        synchronized=False,
        fold_axes=True,
        sort_descending="Sort",
        sort_field="Sub-Category",
        sort_mode="computed",
        panes=[
            {
                "axis": "Profitable Orders",
                "mark_type": "Bar",
                "color": "Measure Names",
                "size": "% of Total Sales",
                "detail": "Sub-Category",
                "labels": ["Sub-Category", "Profitable Orders"],
                "tooltip": ["SUM(Sales)", "Profitable Orders"],
                "mark_style": {
                    "size": "1.5",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                },
                "mark_sizing": {
                    "mark-sizing-setting": "marks-scaling-on",
                    "mark-alignment": "mark-alignment-right",
                    "use-custom-mark-size": False,
                    "custom-mark-size-in-axis-units": 1.0,
                },
            },
            {
                "axis": "Non Profitable Orders",
                "mark_type": "Bar",
                "color": "Measure Names",
                "size": "% of Total Sales",
                "detail": "Sub-Category",
                "tooltip": ["SUM(Sales)", "Profitable Orders"],
                "mark_style": {
                    "size": "1.5",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                },
                "mark_sizing": {
                    "mark-sizing-setting": "marks-scaling-on",
                    "mark-alignment": "mark-alignment-right",
                    "use-custom-mark-size": False,
                    "custom-mark-size-in-axis-units": 1.0,
                },
            },
        ],
        filters=[
            {
                "column": "Segment",
                "values": ["Consumer", "Corporate", "Home Office"],
            }
        ],
        table_calc_overrides=overrides,
    )

    # Author palette: pink profitable share, warm grey remainder.
    def full_ref(expression: str) -> str:
        import json

        ci = editor.field_registry.parse_expression(expression)
        return json.dumps(editor.field_registry.resolve_full_reference(ci.instance_name))

    editor.set_datasource_color_palette(
        "Measure Names",
        {full_ref(expr): color for expr, color in MEASURE_NAMES_PALETTE.items()},
        is_measure_names=True,
    )

    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_axes=True,
        hide_zeroline=True,
        # Fixed-width marks aligned to the right edge of each Sub-Category slot
        # give the variable-width mekko columns.
        axis_style={
            "encodings": [
                {
                    "field": "% Total Sales Cumulative",
                    "scope": "cols",
                    "class": "0",
                    "min": "-0.05",
                    "max": "1.05",
                    "range-type": "fixed",
                },
                {
                    "field": "Non Profitable Orders",
                    "scope": "rows",
                    "class": "0",
                    "reverse": "true",
                    "field-type": "quantitative",
                },
            ],
        },
        pane_mark_style={
            "mark-labels-show": "true",
            "mark-labels-cull": "true",
            "has-stroke": "true",
            "stroke-color": "#ffffff",
        },
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        size_style=None,
    )

    # Constant zero line separating the profitable and non-profitable bars.
    editor.add_reference_line(
        "Viz",
        axis_field="Profitable Orders",
        value_field="Profitable Orders",
        formula="constant",
        scope="per-pane",
        label_type="none",
        probability=None,
        pane_index=0,
    )
    editor.configure_reference_line_style(
        "Viz",
        "refline0",
        {
            "line-visibility": "on",
            "line-pattern-only": "solid",
            "stroke-size": "5",
            "stroke-color": "#000000",
            "fill-above": "#00000000",
            "fill-below": "#00000000",
        },
    )

    editor.set_worksheet_title("Viz", "")

    # --- Dashboard ----------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 800, "y": 1231, "w": 98400, "h": 87692},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "#WOW21 - Week 13",
                        "font_alignment": "1",
                        "font_size": "10",
                    }
                ],
                "absolute": {"x": 800, "y": 93846, "w": 98400, "h": 4923},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=800,
        height=400,
        layout=layout,
        worksheet_names=["Viz"],
    )
    editor.set_window_state("Viz", hidden=False)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
