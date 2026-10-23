"""Rebuild WW35 "How much change has occurred?" from the locked Hyper extract.

The challenge (Luke Stanke, built by Donna Coles) compares 2020 and 2021 Sales
per Sub-Category on one row: a grey 2020 bar with a coloured 2021 dot sitting on
top of it, plus the 2021 sales value and the % change as a label.

Chain:
  data (Order Date, Sub-Category, Sales)
  → filter Order Date (YEAR) to 2020 + 2021 (context filter, before the LoDs)
  → 2021 Sales = {FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2021 THEN [Sales] END)}
  → 2020 Sales = {FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2020 THEN [Sales] END)}
  → % Difference = (SUM([2021 Sales]) - SUM([2020 Sales])) / SUM([2020 Sales])
  → Rows: Sub-Category (sorted DESC by 2021 Sales) / discrete SUM(2021 Sales)
  → Columns: SUM(Sales) twice, synchronised and folded into one dual axis
  → pane 1 = Bar coloured by YEAR(Order Date) (2021 first → 2021 on top of 2020)
  → pane 2 = Circle coloured by YEAR(Order Date (copy)) + label = % Difference
  → dashboard: the "Viz" sheet in a fixed 700x800 layout with the challenge
    footer credits.

Only the packaged extract under ``inputs/`` is read; the author workbook is
never opened here.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = next((HERE / "inputs").glob("*.hyper"))
DASHBOARD = "2021_09_01_WW35_Change_in_Sales"
SHEET = "Viz"

BAR_COLOR_2021 = "#bab0ac"
BAR_COLOR_2020 = "#e15759"
DOT_COLOR_2021 = "#4e79a7"
DOT_COLOR_2020 = "#e15759"

SALES_2021 = "{FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2021 THEN [Sales] END)}"
SALES_2020 = "{FIXED [Sub-Category]: SUM(IF YEAR([Order Date])=2020 THEN [Sales] END)}"
PCT_DIFFERENCE = (
    "(SUM([2021 Sales])-SUM([2020 Sales]))/SUM([2020 Sales])"
)


def build() -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")

    editor.add_calculated_field(
        "2021 Sales",
        SALES_2021,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    # The author shows the 2021 value as a discrete (blue) pill beside
    # Sub-Category. A discrete pill is an ordinal measure, so the same value
    # needs a second field declared ordinal; wrapping the LoD in SUM() keeps
    # it an aggregate so the pill resolves to SUM(2021 Sales).
    editor.add_calculated_field(
        "2021 Sales (discrete)",
        "SUM([2021 Sales])",
        datatype="real",
        role="measure",
        field_type="ordinal",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "2020 Sales",
        SALES_2020,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "% Difference",
        PCT_DIFFERENCE,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*+0%;-0%",
    )
    # A copy of Order Date drives the circle pane's colour so the bar pane can
    # keep its own YEAR(Order Date) palette.
    editor.add_calculated_field(
        "Order Date (copy)",
        "[Order Date]",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )

    # Tableau draws the first colour member in front. Business period labels
    # give Current before Prior without a private XML/manual-sort mutation.
    for period in ("Bar Period", "Dot Period"):
        editor.add_calculated_field(period,
            'IF YEAR([Order Date])=2021 THEN "Current (2021)" ELSE "Prior (2020)" END',
            datatype="string", role="dimension", field_type="nominal")
    editor.add_worksheet(SHEET)
    editor.configure_layered_chart(
        SHEET,
        columns=["SUM(Sales)", "SUM(Sales)"],
        rows=["Sub-Category", "2021 Sales (discrete)"],
        axis_shelf="columns",
        synchronized=True,
        fold_axes=True,
        sort_descending="SUM(2021 Sales)",
        sort_field="Sub-Category",
        sort_mode="computed",
        filters=[
            {
                "column": "YEAR(Order Date)",
                "values": [2020, 2021],
                "context": True,
            }
        ],
        panes=[
            # The bar pane owns the first axis and the circle pane the second,
            # exactly as the author's workbook does (pane id=1 Bar, pane id=2
            # x-index=1 with the circle). Later panes are drawn on top, so the
            # 2021 dot sits over the 2020 bar.
            {
                "axis": "SUM(Sales)",
                "mark_type": "Bar",
                "breakdown": "off",
                "color": "Bar Period",
                "color_map": {"Current (2021)": BAR_COLOR_2021, "Prior (2020)": BAR_COLOR_2020},
                "mark_style": {"size": "0.4497", "mark-labels-show": "false"},
            },
            {
                "axis": "SUM(Sales)",
                "mark_type": "Circle",
                "breakdown": "off",
                "color": "Dot Period",
                "color_map": {"Current (2021)": DOT_COLOR_2021, "Prior (2020)": DOT_COLOR_2020},
                "label": "% Difference",
                "mark_style": {
                    "size": "0.9",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "range",
                    "mark-labels-range-scope": "cell",
                    "mark-labels-range-field": "Dot Period",
                    "mark-labels-range-max": "false",
                    "mark-labels-range-min": "true",
                },
            },
        ],
    )

    tooltip_runs = [
        {"field": "Sub-Category", "bold": True},
        {"text": "\nSales in 2021 :"},
        {"field": "2021 Sales (discrete)", "bold": True},
        {"text": "\nSales in 2020 :"},
        {"field": "2020 Sales", "bold": True},
        {"text": "\n% Difference :"},
        {"field": "% Difference", "bold": True},
    ]
    # The author's tooltip is identical on both panes.
    editor.configure_custom_tooltip(SHEET, tooltip_runs, pane_index=0)
    editor.configure_custom_tooltip(SHEET, tooltip_runs, pane_index=1)
    editor.configure_worksheet_style(
        SHEET,
        hide_gridlines=True,
        hide_row_field_labels=True,
        axis_style={"per_field":[{"field":"SUM(Sales)","class":"1","scope":"cols","attr":"display","value":"false"}]},
        hide_borders=True,
        hide_zeroline=True,
        cell_formats=[
            {"field": "Sub-Category", "attr": "height", "value": "41"},
            {"field": "2021 Sales (discrete)", "attr": "height", "value": "45"},
        ],
    )
    editor.set_worksheet_rich_title(
        SHEET,
        [
            {
                "text": "How much change has occurred between Sales of Sub-Categories in ",
                "bold": True,
                "fontsize": 12,
            },
            {"text": "2020", "bold": True, "fontcolor": BAR_COLOR_2020, "fontsize": 12},
            {"text": " and ", "bold": True, "fontsize": 12},
            {"text": "2021", "bold": True, "fontcolor": DOT_COLOR_2021, "fontsize": 12},
        ],
    )

    layout = {
        "type": "container",
        "direction": "vertical",
        "style": {"padding": 0},
        "children": [
            {
                "type": "worksheet",
                "name": SHEET,
                "fit": "entire",
                "show_title": True,
                "style": {"margin": 4},
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 30,
                "children": [
                    {
                        "type": "text",
                        "text": "CHALLENGE BY : LUKE STANKE",
                        "font_size": 8,
                        "font_color": DOT_COLOR_2021,
                        "bold": True,
                    },
                    {
                        "type": "text",
                        "text": "#WOW2021  |  WEEK 35",
                        "font_size": 8,
                        "font_color": DOT_COLOR_2021,
                        "bold": True,
                    },
                    {
                        "type": "text",
                        "text": "RECREATED WITH : cwtwb",
                        "font_size": 8,
                        "font_color": DOT_COLOR_2021,
                        "bold": True,
                    },
                ],
            },
            {
                "type": "text",
                "text": "http://www.workout-wednesday.com/2021w35/",
                "font_size": 8,
                "fixed_size": 25,
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD, width=700, height=800, worksheet_names=[SHEET], layout=layout
    )

    editor.set_window_state(DASHBOARD, zoom_entire_view=True)
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
