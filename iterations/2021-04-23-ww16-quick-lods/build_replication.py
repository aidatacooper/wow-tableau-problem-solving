"""Rebuild the WW16 Quick LoDs dual-axis chart.

The challenge (Tableau 2021.1's Quick LoDs) asks for one sheet: a dual-axis
chart showing each Sub-Category's sales against the Sub-Category Average Sales
by Category, with the percent difference labelled and the bars coloured by
whether they beat that average.

The article's chain:

- ``Sales (Sub-Category) = { FIXED [Sub-Category]: SUM([Sales]) }`` — the first
  Quick LoD (sales per Sub-Category).
- ``Sales (Sub-Category) (Category) = { FIXED [Category]:
  AVG([Sales (Sub-Category)]) }`` — the second Quick LoD, edited from SUM to
  AVG, giving the average Sub-Category sales within each Category.
- ``Difference = (SUM([Sales]) - SUM([Sales (Sub-Category) (Category)])) /
  SUM([Sales (Sub-Category) (Category)])`` formatted ``▲0%;▼0%``.
- ``Colour = [Difference] > 0`` drives the bar palette (teal above, grey below).
- ``Above | Below = IF [Difference] > 0 THEN 'Above' ELSE 'Below' END`` for the
  tooltip.

The chart is a dual axis on Columns: Sales as Bars (coloured by Colour, labelled
with Difference) and the Category average as a GanttBar sized to full height in
light grey behind them, with Category and Sub-Category on Rows.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/Orders (Sample - Superstore).hyper"
DASHBOARD = "2021_04_21_WW16_Quick_LODs"

TEAL = "#108080"
GREY = "#bab0ac"
AVG_BAR = "#d4d4d4"


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Quick LoD chain ---------------------------------------------------
    editor.add_calculated_field(
        "Sales (Sub-Category)",
        "{ FIXED [Sub-Category]: SUM([Sales]) }",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Sales (Sub-Category) (Category)",
        "{ FIXED [Category]: AVG([Sales (Sub-Category)]) }",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "Difference",
        "(SUM([Sales])- SUM([Sales (Sub-Category) (Category)]))"
        " / SUM([Sales (Sub-Category) (Category)])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*▲0%;▼0%",
    )
    editor.add_calculated_field(
        "Colour",
        "[Difference]>0",
        datatype="boolean",
        role="measure",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Above | Below",
        "IF [Difference]>0 THEN 'Above' ELSE 'Below' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )

    # --- Single dual-axis sheet -------------------------------------------
    editor.add_worksheet("Viz")
    editor.configure_dual_axis(
        "Viz",
        mark_type_1="Bar",
        mark_type_2="GanttBar",
        dual_axis_shelf="cols",
        columns=["SUM(Sales)", "SUM(Sales (Sub-Category) (Category))"],
        rows=["Category", "Sub-Category"],
        color_1="Colour",
        label_1="Difference",
        size_value_2="1.9890055656433105",
        mark_color_2=AVG_BAR,
        synchronized=True,
        show_labels=True,
        hide_axes=True,
        sort_descending="SUM(Sales)",
        sort_field="Sub-Category",
    )
    # The boolean palette lives on the datasource mark rule.
    editor.set_datasource_color_palette("Colour", {"true": TEAL, "false": GREY})
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        pane_datalabel_style={"color-mode": "auto", "font-size": "8"},
        # The GanttBar pane draws the Category average as a full-height grey
        # backdrop with no labels; the Difference label belongs to the Bar pane.
        panes_style={
            "1": {
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "true"},
            },
            "2": {
                "mark_style": {
                    "mark-labels-show": "false",
                    "mark-labels-cull": "true",
                    "size": "1.9890055656433105",
                    "mark-color": AVG_BAR,
                },
            },
        },
    )

    # Author's tooltip: Category | Sub-Category, the sales, then the difference
    # with the Above/Below word and the Category average.
    tooltip_runs = [
        {"field": "Category", "bold": True},
        {"text": " | "},
        {"field": "Sub-Category", "bold": True},
        {"text": "\n"},
        {"field": "SUM(Sales)", "bold": True},
        {"text": "\n\n"},
        {"field": "Difference", "bold": True},
        {"text": " "},
        {"field": "Above | Below", "bold": True},
        {"text": " the average category sales of "},
        {"field": "SUM(Sales (Sub-Category) (Category))", "bold": True},
    ]
    editor.configure_custom_tooltip("Viz", tooltip_runs, pane_index=0)
    editor.configure_custom_tooltip("Viz", tooltip_runs, pane_index=1)

    # --- Dashboard ---------------------------------------------------------
    layout = {
        "type": "container",
        "direction": "floating",
        "children": [
            {
                "type": "text",
                "runs": [
                    {"text": "#WOW2021 W16: Can you use "},
                    {"text": "Quick LODs", "bold": True},
                    {"text": " to recreate this view?"},
                ],
                "font_size": "24",
                "font_color": "#333333",
                "absolute": {"x": 500, "y": 1000, "w": 99000, "h": 8000},
            },
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 500, "y": 10000, "w": 99000, "h": 85000},
            },
            {
                "type": "text",
                "runs": [{"text": "#WOW2021 W16", "font_size": "10"}],
                "absolute": {"x": 500, "y": 96000, "w": 30000, "h": 3000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Data | Superstore",
                        "font_size": "10",
                        "font_alignment": "1",
                    }
                ],
                "absolute": {"x": 35000, "y": 96000, "w": 30000, "h": 3000},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "Challenge by @_Lorna_Brown",
                        "font_size": "10",
                        "font_alignment": "2",
                    }
                ],
                "absolute": {"x": 66000, "y": 96000, "w": 33000, "h": 3000},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=800,
        height=700,
        layout=layout,
        worksheet_names=["Viz"],
    )
    editor.set_window_state("Viz", hidden=False)
    editor.set_worksheet_title("Viz", "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
