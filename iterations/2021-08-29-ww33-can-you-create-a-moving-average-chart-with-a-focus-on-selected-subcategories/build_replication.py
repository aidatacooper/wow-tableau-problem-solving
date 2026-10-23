"""Rebuild the WW33 parameterised moving-average chart with a set focus.

The article asks for one monthly chart per Sub-Category where:

* ``pPrior`` / ``pPost`` (integers 1..6, step 1, default 3) define the window;
  ``pPrior`` counts the current month, so the WINDOW_AVG start offset is
  ``(-1*[pPrior])+1``.
* Five small Sub-Categories are grouped into ``Misc`` (the article text says
  three, the author workbook groups five), so the chart has 13 lines.
* A set on ``Sub-Category (group)`` drives colour and size: members of the set
  are coloured and thick, everything else is grey and thin.  The set control
  lives on the dashboard.
* A shaded band behind the lines is the unstacked area between the per-month
  ``WINDOW_MAX([Moving Avg])`` and ``WINDOW_MIN([Moving Avg])`` across all
  Sub-Categories (nested table calcs: the inner Moving Avg addresses the month,
  the outer window addresses Sub-Category).

The builder reads only ``case.yaml``, ``analysis.md``, the locked extract and
public ``cwtwb`` APIs.  The author workbook is never opened here.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = next((HERE / "inputs").glob("*.hyper"))
DASHBOARD = "2021_08_18_WW33_Moving_Avg"
SHEET = "Viz"
DATA_SHEET = "Data"
MISC_MEMBERS = ["Art", "Envelopes", "Fasteners", "Labels", "Supplies"]
MONTH = "MONTHTRUNC(Order Date)"
DISCRETE_MONTH = "DISCRETE(MONTHTRUNC(Order Date))"

# Author palette, keyed by Sub-Category (group).  The default (out-of-set)
# colour is grey; the size shelf shrinks the out-of-set marks.
CATEGORY_COLORS = {
    "Accessories": "#a0cbe8",
    "Appliances": "#ffbe7d",
    "Binders": "#59a14f",
    "Bookcases": "#8cd17d",
    "Chairs": "#4e79a7",
    "Copiers": "#b6992d",
    "Furnishings": "#f1ce63",
    "Machines": "#499894",
    "Misc": "#86bcb6",
    "Paper": "#f28e2b",
    "Phones": "#ff9d9a",
    "Storage": "#e15759",
    "Tables": "#79706e",
}


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")

    # --- Parameters -------------------------------------------------------
    for name in ("pPrior", "pPost"):
        editor.add_parameter(
            name,
            datatype="integer",
            default_value="3",
            domain_type="range",
            min_value="1",
            max_value="6",
            granularity="1",
        )

    # --- Group: five small Sub-Categories collapse into Misc ---------------
    editor.add_group(
        "Sub-Category (group)",
        "Sub-Category",
        {"Misc": MISC_MEMBERS},
        default_value=None,
        internal_name="[Sub-Category (group)]",
    )

    # --- Set over the grouped dimension ------------------------------------
    editor.add_set(
        "Sub-Category (group) Set",
        "Sub-Category (group)",
        members=[
            "Accessories",
            "Appliances",
            "Binders",
            "Bookcases",
            "Chairs",
            "Copiers",
            "Furnishings",
            "Machines",
            "Misc",
            "Paper",
            "Phones",
            "Storage",
            "Tables",
        ],
    )

    # --- Table calculations ------------------------------------------------
    editor.add_calculated_field(
        "Moving Avg",
        "WINDOW_AVG(SUM([Sales]), (-1*[Parameters].[pPrior])+1, "
        "[Parameters].[pPost])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        # The month addressing is attached per instance by
        # configure_layered_chart(table_calc_overrides=...); the field-level
        # metadata only has to declare that this is a table calculation.
        table_calc="Rows",
        default_format='n"$"#,##0;-"$"#,##0',
    )
    editor.add_calculated_field(
        "Window Max Avg",
        "WINDOW_MAX([Moving Avg])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Window Min Avg",
        "WINDOW_MIN([Moving Avg])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        table_calc="Rows",
    )

    # Nested addressing: Moving Avg computes along the month, the two window
    # extrema compute across Sub-Category while inheriting that month context.
    month_address = {"ordering-type": "Field", "ordering-field": MONTH}
    nested = [
        {"ordering-type": "Field", "ordering-field": "Sub-Category (group)"},
        {"field": "Moving Avg", **month_address},
    ]
    overrides = {
        "Moving Avg": [month_address],
        "Window Max Avg": nested,
        "Window Min Avg": nested,
    }
    # The inspection sheet shows a discrete month, so its table calcs address
    # that instance instead of the continuous one used by the chart.
    discrete_address = {"ordering-type": "Field", "ordering-field": DISCRETE_MONTH}
    data_overrides = {
        "Moving Avg": [discrete_address],
        "Window Max Avg": [
            {"ordering-type": "Field", "ordering-field": "Sub-Category (group)"},
            {"field": "Moving Avg", **discrete_address},
        ],
        "Window Min Avg": [
            {"ordering-type": "Field", "ordering-field": "Sub-Category (group)"},
            {"field": "Moving Avg", **discrete_address},
        ],
    }

    # --- Data sheet (the author's inspection sheet, used for CSV evidence) --
    editor.add_worksheet(DATA_SHEET)
    editor.configure_layered_chart(
        DATA_SHEET,
        columns=["Measure Names"],
        rows=[DISCRETE_MONTH, "Sub-Category (group)"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    "SUM(Sales)",
                    "Moving Avg",
                    "Window Max Avg",
                    "Window Min Avg",
                ],
            }
        ],
        table_calc_overrides=data_overrides,
    )
    editor.set_measure_name_aliases(
        DATA_SHEET,
        {
            "SUM(Sales)": "Sales",
            "Moving Avg": "Moving Avg",
            "Window Max Avg": "Window Max Avg",
            "Window Min Avg": "Window Min Avg",
        },
    )

    # --- Viz sheet: grey band + coloured lines, dual folded axis -----------
    editor.add_worksheet(SHEET)
    editor.configure_layered_chart(
        SHEET,
        columns=[MONTH],
        rows=["Moving Avg", "Multiple Values"],
        axis_shelf="rows",
        synchronized=True,
        fold_axes=True,
        panes=[
            {
                "axis": "Moving Avg",
                "mark_type": "Line",
                "color": "Sub-Category (group) Set",
                "color_extra": ["Sub-Category (group)"],
                "size": "Sub-Category (group) Set",
                "detail": "Sub-Category (group)",
                "tooltip": ["SUM(Sales)"],
                "mark_sizing_off": True,
                "mark_style": {"mark-color": "#898989"},
            },
            {
                "axis": "Multiple Values",
                "mark_type": "Area",
                "measure_values": ["Window Min Avg", "Window Max Avg"],
                "color": "Measure Names",
                "detail": "Sub-Category (group)",
                "mark_sizing_off": True,
                "selection_relaxation": "disallow",
                "mark_style": {"mark-transparency": "255"},
            },
        ],
        table_calc_overrides=overrides,
    )

    # Set palette: in-set members coloured, out-of-set grey.  The rendered
    # colour comes from the compound (set x Sub-Category) palette; the single
    # field palettes are the author's fallbacks for the legend entries.
    editor.set_datasource_color_palette(
        "Sub-Category (group) Set", {"true": "#4e79a7", "false": "#a2a2a2"}
    )
    editor.set_datasource_color_palette("Sub-Category (group)", CATEGORY_COLORS)
    editor.set_compound_color_palette(
        ["Sub-Category (group) Set", "Sub-Category (group)"],
        [
            {"values": [True, group], "color": color}
            for group, color in CATEGORY_COLORS.items()
        ]
        + [
            {"values": [False, group], "color": "#bab0ac"}
            for group in CATEGORY_COLORS
        ],
    )
    # Measure Names palette: Window Min Avg white (it is the "lower" area that
    # paints over the max band), Window Max Avg pale grey.
    mn = {}
    for expression, color in (
        ("Window Min Avg", "#ffffff"),
        ("Window Max Avg", "#eeeeee"),
    ):
        ci = editor.field_registry.parse_expression(expression)
        reference = editor.field_registry.resolve_full_reference(ci.instance_name)
        mn['"' + reference + '"'] = color
    editor.set_datasource_color_palette("Measure Names", mn, is_measure_names=True)

    editor.configure_worksheet_style(
        SHEET,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        size_style={
            "field": "Sub-Category (group) Set",
            "type": "catsize",
            "min_size": "0.2",
            "max_size": "1",
            "reverse": True,
        },
        axis_style={
            "render-fold-reversed": "true",
            "per_field": [
                {
                    "field": MONTH,
                    "attr": "title",
                    "scope": "cols",
                    "class": "0",
                    "value": "",
                },
                {
                    "field": "Multiple Values",
                    "attr": "display",
                    "scope": "rows",
                    "class": "0",
                    "value": "false",
                },
            ],
        },
    )
    editor.configure_worksheet_style(
        DATA_SHEET,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_table_dividers=True,
    )

    # --- Dashboard ---------------------------------------------------------
    def p(x, y, w, h):
        return {
            "x": round(x / 600 * 100000),
            "y": round(y / 600 * 100000),
            "w": round(w / 600 * 100000),
            "h": round(h / 600 * 100000),
        }

    zones = [
        {
            "type": "text",
            "text": (
                "Can you create a moving average chart with a focus on "
                "selected sub-categories?"
            ),
            "font_size": 12,
            "bold": True,
            "absolute": p(8, 8, 584, 62),
        },
        {
            "type": "set_control",
            "worksheet": SHEET,
            "field": "Sub-Category (group) Set",
            "mode": "checkdropdown",
            "absolute": p(8, 70, 195, 110),
        },
        {
            "type": "paramctrl",
            "parameter": "pPrior",
            "mode": "slider",
            "caption": "Moving Average Prior Months\nIncluding Current Month",
            "absolute": p(203, 70, 195, 110),
        },
        {
            "type": "paramctrl",
            "parameter": "pPost",
            "mode": "slider",
            "caption": "Moving Average Post Months",
            "absolute": p(398, 70, 194, 110),
        },
        {
            "type": "worksheet",
            "name": SHEET,
            "show_title": False,
            "fit": "entire",
            "absolute": p(8, 180, 584, 348),
        },
        {
            "type": "text",
            "text": "CHALLENGE BY : LORNA BROWN",
            "font_size": 8,
            "absolute": p(8, 528, 211, 32),
        },
        {
            "type": "text",
            "text": "#WOW2021 | WEEK 33",
            "font_size": 8,
            "absolute": p(219, 528, 164, 32),
        },
        {
            "type": "text",
            "text": "RECREATED BY : DONNA COLES",
            "font_size": 8,
            "absolute": p(383, 528, 209, 32),
        },
        {
            "type": "text",
            "text": "http://www.workout-wednesday.com/2021w33tab/",
            "font_size": 8,
            "hyperlink": "http://www.workout-wednesday.com/2021w33tab/",
            "absolute": p(8, 560, 584, 32),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=600,
        height=600,
        worksheet_names=[SHEET],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    editor.set_active_dashboard(DASHBOARD)

    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(parents=True, exist_ok=True)
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
