"""Rebuild the WW12 Comparative Quantity Analysis with INCLUDE/EXCLUDE LoDs.

The challenge asks for two side-by-side bar charts by Sub-Category: the average
quantity inclusive of manufacturer, and the variance between each Sub-Category's
average and the average of a user-selected Sub-Category. Clicking a bar drives a
parameter action that reselects the comparison baseline.

The article publishes two solutions. This builder follows the LoD route the
challenge was actually testing (the parameter action, not FIXED, is required by
the challenge, and FIXED LoDs are explicitly forbidden):

    Qty Inc Manufacturer       = {INCLUDE [Manufacturer] : SUM([Quantity])}
    Avg Qty Inc Manufacturer   = AVG([Qty Inc Manufacturer])
    Is Selected Sub Cat        = [Sub-Category] = [pSelectedSubCat]
    Selected Qty               = IF [Is Selected Sub Cat] THEN [Quantity] END
    Selected Qty Inc Manuf     = {INCLUDE [Manufacturer] : SUM([Selected Qty])}
    Overall Selected Qty       = {EXCLUDE [Sub-Category], [Is Selected Sub Cat]
                                  : AVG([Selected Qty Inc Manufacturer])}
    Variance                   = AVG([Qty Inc Manufacturer])
                                 - MIN([Overall Selected Qty Inc Manufacturer])

The two bars are two panes of one worksheet sharing the Sub-Category row axis:
the Avg pane colours by ``Is Selected Sub Cat`` (boolean palette) and the
Variance pane colours by ``Variance`` (continuous diverging palette, ~75%
opacity), matching the author's side-by-side layout in a single sheet.

``configure_layered_chart`` folds the two measures onto the column axis with
native pane entries, so each measure keeps an independent axis domain. A
parameter action on click sets ``pSelectedSubCat`` from the clicked
``Sub-Category``; a second filter action maps True to False so Tableau's default
selection highlight never overrides the colour encodings.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/Superstore with Manufacturer.hyper"
DASHBOARD = "2021_03_24_WW12_Comparative_Qty"

# The selected/not-selected palette mirrors the author's boolean encoding:
# teal for the selected Sub-Category, neutral grey for everything else.
SELECTED_COLORS = {"true": "#73b2ad", "false": "#d5d5d5"}


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # --- Parameter driving the comparison baseline --------------------------
    editor.add_parameter(
        "pSelectedSubCat",
        datatype="string",
        default_value="Fasteners",
        domain_type="any",
    )

    # --- INCLUDE / EXCLUDE LoD chain (the challenge's actual subject) -------
    editor.add_calculated_field(
        "Qty Inc Manufacturer",
        "{INCLUDE [Manufacturer] : SUM([Quantity])}",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Avg Qty Inc Manufacturer",
        "AVG([Qty Inc Manufacturer])",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Is Selected Sub Cat",
        "[Sub-Category]=[pSelectedSubCat]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Selected Qty",
        "IF [Is Selected Sub Cat] THEN [Quantity] END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Selected Qty Inc Manufacturer",
        "{INCLUDE [Manufacturer] : SUM([Selected Qty])}",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Overall Selected Qty Inc Manufacturer",
        "{EXCLUDE [Sub-Category], [Is Selected Sub Cat] : "
        "AVG([Selected Qty Inc Manufacturer])}",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Variance",
        "AVG([Qty Inc Manufacturer]) - MIN([Overall Selected Qty Inc Manufacturer])",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "TOOLTIP Variance",
        "ABS([Variance])",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "TOOLTIP more or less",
        "IF [Variance] <= 0 THEN 'less' ELSE 'more' END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    # Constants used only by the "Unhighlight" filter action mapping.
    editor.add_calculated_field(
        "True",
        "True",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "False",
        "False",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )

    tooltip = [
        "Sub-Category",
        "Avg Qty Inc Manufacturer",
        "TOOLTIP Variance",
        "TOOLTIP more or less",
    ]

    # --- One worksheet, two panes: Avg Qty | Variance ----------------------
    editor.add_worksheet("Viz")
    editor.configure_layered_chart(
        "Viz",
        rows=["Sub-Category"],
        columns=["Avg Qty Inc Manufacturer", "Variance"],
        axis_shelf="columns",
        synchronized=False,
        fold_axes=False,
        sort_descending="Avg Qty Inc Manufacturer",
        sort_field="Sub-Category",
        sort_mode="computed",
        panes=[
            {
                "axis": "Avg Qty Inc Manufacturer",
                "mark_type": "Bar",
                "color": "Is Selected Sub Cat",
                "color_map": SELECTED_COLORS,
                "tooltip": tooltip,
                "selection_relaxation": "disallow",
            },
            {
                "axis": "Variance",
                "mark_type": "Bar",
                "color": "Variance",
                "tooltip": tooltip,
                "mark_style": {"mark-transparency": "190"},
                "selection_relaxation": "disallow",
            },
        ],
    )
    editor.configure_custom_tooltip(
        "Viz",
        [
            {"field": "Sub-Category", "bold": True, "fontcolor": "#555555"},
            {"text": " sold an average of ", "fontcolor": "#555555"},
            {"field": "Avg Qty Inc Manufacturer", "bold": True, "fontcolor": "#555555"},
            {"text": " units. This was ", "fontcolor": "#555555"},
            {"field": "TOOLTIP Variance", "bold": True, "fontcolor": "#555555"},
            {"text": " ǅ ", "fontcolor": "#555555"},
            {"field": "TOOLTIP more or less", "bold": True, "fontcolor": "#555555"},
            {"text": " when compared to ", "fontcolor": "#555555"},
            {"text": "the selected Sub-Category", "bold": True, "fontcolor": "#555555"},
        ],
        pane_index=0,
    )
    editor.configure_custom_tooltip(
        "Viz",
        [
            {"field": "Sub-Category", "bold": True, "fontcolor": "#555555"},
            {"text": " sold an average of ", "fontcolor": "#555555"},
            {"field": "Avg Qty Inc Manufacturer", "bold": True, "fontcolor": "#555555"},
            {"text": " units. This was ", "fontcolor": "#555555"},
            {"field": "TOOLTIP Variance", "bold": True, "fontcolor": "#555555"},
            {"text": " ǅ ", "fontcolor": "#555555"},
            {"field": "TOOLTIP more or less", "bold": True, "fontcolor": "#555555"},
            {"text": " when compared to ", "fontcolor": "#555555"},
            {"text": "the selected Sub-Category", "bold": True, "fontcolor": "#555555"},
        ],
        pane_index=1,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_borders=True,
        color_style={
            "field": "Variance",
            "palette": "orange-blue-diverging",
            "center": 0,
        },
        axis_style={
            "per_field": [
                {
                    "field": "Avg Qty Inc Manufacturer",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Avg. Total Quantity inclusive of Manufacturer",
                },
                {
                    "field": "Variance",
                    "scope": "cols",
                    "attr": "title",
                    "value": "Variance",
                },
            ]
        },
    )
    editor.set_worksheet_title("Viz", "")

    # --- Dashboard with the click-to-compare parameter action --------------
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
                        "text": "CHALLENGE BY : SEAN MILLER",
                        "bold": True,
                        "font_color": "#73b2ad",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 800, "y": 88923, "w": 32800, "h": 4923},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "#WOW2021  |  WEEK 12",
                        "bold": True,
                        "font_alignment": "1",
                        "font_color": "#73b2ad",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 33600, "y": 88923, "w": 32800, "h": 4923},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "RECREATED BY : DONNA COLES",
                        "bold": True,
                        "font_alignment": "2",
                        "font_color": "#73b2ad",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 66400, "y": 88923, "w": 32800, "h": 4923},
            },
            {
                "type": "text",
                "runs": [
                    {
                        "text": "http://www.workout-wednesday.com/2021w12tab/",
                        "font_alignment": "1",
                        "font_size": "8",
                    }
                ],
                "absolute": {"x": 800, "y": 93846, "w": 98400, "h": 4923},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=650,
        layout=layout,
        worksheet_names=["Viz"],
    )

    # Clicking a Sub-Category bar sets the comparison baseline.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Viz",
        source_field="Sub-Category",
        target_parameter="pSelectedSubCat",
        aggregation="attr",
        caption="Parameter1",
    )
    # Map True -> False so the click never leaves Tableau's default selection
    # highlight on top of the authored colour encodings (the author's
    # "Unhighlight" action; the mapping can never match, so it never filters).
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Viz",
        target_sheet="Viz",
        field_mappings={"True": "False"},
        caption="Unhighlight",
    )

    editor.set_window_state("Viz", hidden=False)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
