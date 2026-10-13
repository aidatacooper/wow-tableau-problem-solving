"""Rebuild the WW26 "Profitability with Dual Axis Charts" Pareto workbook.

The challenge (Luke Stanke, built by Donna Coles) plots cumulative profit
against the cumulative percentage of orders on an unsynchronised dual axis: a
cumulative-profit line coloured by whether the order was profitable, and a
sales bar behind it. The subtitle reports the share of orders that were
profitable and how much the unprofitable ones cut potential profitability.

Chain:
  data (Order ID, Sales, Profit)
  → Count Orders = COUNTD([Order ID])
  → Cumulative Order Count = RUNNING_SUM([Count Orders])
  → Total Order Count = WINDOW_SUM([Count Orders])
  → Cumulative % of Total Orders = [Cumulative Order Count]/[Total Order Count]
  → Cumulative Profit = RUNNING_SUM(SUM([Profit]))
  → Profit is +ve = SUM([Profit]) > 0
  → Profitable Marker = LOOKUP([Profit is +ve],-1) AND NOT([Profit is +ve])
  → % of Total Profitable = WINDOW_MAX(IF marker THEN cum% END)
  → Total Cumulative Profit = WINDOW_MAX(IF LAST()=0 THEN [Cumulative Profit] END)
  → Potential Profitability Decrease =
      WINDOW_MAX(IF marker THEN ([Cumulative Profit]-[Total Cumulative Profit])
                 /[Cumulative Profit] END)
  → Viz: Order ID on Detail, sorted by Profit descending; Cumulative Profit and
    Sales on the Rows shelf (unsynchronised dual axis), Cumulative % of Total
    Orders on Columns; a line pane (coloured by Profit is +ve) over a bar pane
  → dashboard: title + the parameterised subtitle text
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_0ootdtt1hkoyir17nqe8y1cxn2lr.hyper"
DASHBOARD = "2021_06_30_WW26_Pareto_Profitability"

POSITIVE = "#5b9bd5"
NEGATIVE = "#f2a63b"
BAR_COLOR = "#898989"

CUMULATIVE_PROFIT = "RUNNING_SUM(SUM([Profit]))"
COUNT_ORDERS = "COUNTD([Order ID])"
CUMULATIVE_ORDER_COUNT = "RUNNING_SUM([Count Orders])"
TOTAL_ORDER_COUNT = "WINDOW_SUM([Count Orders])"
CUMULATIVE_PCT = "[Cumulative Order Count]/[Total Order Count]"
PROFIT_POSITIVE = "SUM([Profit]) >0"
PROFITABLE_MARKER = "LOOKUP([Profit is +ve],-1) AND NOT([Profit is +ve])"
PCT_PROFITABLE = "WINDOW_MAX(IF [Profitable Marker] THEN [Cumulative % of Total Orders] END)"
TOTAL_CUMULATIVE_PROFIT = "WINDOW_MAX(IF LAST()=0 THEN [Cumulative Profit] END)"
POTENTIAL_DECREASE = (
    "WINDOW_MAX(IF [Profitable Marker] THEN "
    "([Cumulative Profit]-[Total Cumulative Profit])/[Cumulative Profit] END)"
)

# The author addresses every table calculation by Order ID. Because the
# worksheet never calls table_calc_overrides, the builder keeps the
# auto-generated nested <table-calc> dependency metadata that Cloud needs to
# resolve RUNNING_SUM/WINDOW_MAX/LOOKUP over the sorted Order ID marks. An
# explicit override replaces that metadata and collapses the chart to 100%.
ORDER_ADDRESSING = {"ordering_type": "Field", "ordering_field": "[Order ID]"}


def add_measures(editor: TWBEditor) -> None:
    editor.add_calculated_field(
        "Count Orders",
        COUNT_ORDERS,
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Cumulative Order Count",
        CUMULATIVE_ORDER_COUNT,
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Total Order Count",
        TOTAL_ORDER_COUNT,
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Cumulative % of Total Orders",
        CUMULATIVE_PCT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Cumulative Profit",
        CUMULATIVE_PROFIT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;("$"#,##0)',
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Profit is +ve",
        PROFIT_POSITIVE,
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Profitable Marker",
        PROFITABLE_MARKER,
        datatype="boolean",
        role="measure",
        field_type="nominal",
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "% of Total Profitable",
        PCT_PROFITABLE,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Total Cumulative Profit",
        TOTAL_CUMULATIVE_PROFIT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;("$"#,##0)',
        table_calc=ORDER_ADDRESSING,
    )
    editor.add_calculated_field(
        "Potential Profitability Decrease",
        POTENTIAL_DECREASE,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0%",
        table_calc=ORDER_ADDRESSING,
    )


def build_viz(editor: TWBEditor) -> None:
    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        columns=["Cumulative % of Total Orders"],
        rows=["Cumulative Profit", "SUM(Sales)"],
        axis_shelf="rows",
        fold_axes=True,
        synchronized=False,
        sort_field="Order ID",
        sort_descending="SUM(Profit)",
        sort_mode="computed",
        panes=[
            {
                "axis": "Cumulative Profit",
                "mark_type": "Line",
                "color": "Profit is +ve",
                "color_map": {"true": POSITIVE, "false": NEGATIVE},
                "detail_extra": [
                    "Order ID",
                    "% of Total Profitable",
                    "Potential Profitability Decrease",
                ],
                "tooltip": ["SUM(Sales)", "SUM(Profit)"],
                "mark_sizing_off": True,
            },
            {
                "axis": "SUM(Sales)",
                "mark_type": "Bar",
                "detail_extra": [
                    "Order ID",
                    "% of Total Profitable",
                    "Potential Profitability Decrease",
                ],
                "tooltip": ["SUM(Sales)", "SUM(Profit)"],
                "mark_style": {"mark-color": BAR_COLOR, "size": "0.01"},
                "mark_sizing_off": True,
            },
        ],
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_gridlines=True,
        pane_cell_style={"font-size": "8"},
        axis_style={
            "per_field": [
                {
                    "field": "Cumulative % of Total Orders",
                    "scope": "cols",
                    "attr": "title",
                    "value": "% of Total Orders",
                },
                {
                    "field": "Cumulative Profit",
                    "scope": "rows",
                    "attr": "title",
                    "value": "Cumulative Profit",
                },
            ]
        },
    )
    editor.set_worksheet_rich_title(
        "Viz",
        [
            {
                "text": "PROFITABILITY WITH DUAL AXIS CHART",
                "fontalignment": 1,
            },
            {"text": "\u00c6\n"},
            {
                "text": "Of your orders, <% of Total Profitable> were profitable. "
                        "The remaining orders decreased potential profitability by "
                        "<Potential Profitability Decrease>",
                "fontsize": 11,
            },
        ],
    )


def build_dashboard(editor: TWBEditor) -> None:
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=500,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                {
                    "type": "worksheet",
                    "name": "Viz",
                    "show_title": True,
                    "fit": "entire",
                    "absolute": {
                        "x": 800,
                        "y": 800,
                        "w": 98400,
                        "h": 98400,
                    },
                }
            ],
        },
        worksheet_names=["Viz"],
    )
    editor.set_window_state("Viz", hidden=False, zoom_entire_view=True)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    add_measures(editor)
    build_viz(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
