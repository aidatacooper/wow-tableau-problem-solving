"""Build WW32 from an empty cwtwb workbook and the locked original Hyper."""

from pathlib import Path
import re
import sys


ITERATION_DIR = Path(__file__).resolve().parent


from cwtwb.twb_editor import TWBEditor  # noqa: E402


HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"
DASHBOARD = "2019_08_07_WW32_Step_Area-Chart"


CALCULATIONS = [
    {
        "name": "Month",
        "formula": "MONTH([Order Date])",
        "datatype": "integer",
    },
    {
        "name": "Sales In Month",
        "formula": (
            "{FIXED [Category], DATETRUNC('month', [Order Date]): SUM([Sales])}"
        ),
        "datatype": "real",
    },
    {
        "name": "Sales Next Value",
        "formula": "LOOKUP(SUM([Sales In Month]), 1)",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Sales Diff",
        "formula": "[Sales Next Value] - SUM([Sales In Month])",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Max Diff",
        "formula": "WINDOW_MAX([Sales Diff])",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Min Diff",
        "formula": "WINDOW_MIN([Sales Diff])",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Is Max Value?",
        "formula": "[Sales Diff] = [Max Diff]",
        "datatype": "boolean",
        "table_calc": "Rows",
    },
    {
        "name": "Is Min Value?",
        "formula": "[Sales Diff] = [Min Diff]",
        "datatype": "boolean",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL: Max Diff",
        "formula": "IF [Is Max Value?] THEN [Sales Diff] END",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL: Max Diff + Shift",
        "formula": "LOOKUP([LABEL: Max Diff], -1)",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL: Min Diff",
        "formula": "IF [Is Min Value?] THEN [Sales Diff] END",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL: Min Diff + Shift",
        "formula": "LOOKUP([LABEL: Min Diff], -1)",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL:Sales in Month Max",
        "formula": (
            "IF NOT(ZN([LABEL: Max Diff + Shift]) = 0) "
            "THEN SUM([Sales In Month]) END"
        ),
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL:Sales in Month Min",
        "formula": (
            "IF NOT(ZN([LABEL: Min Diff + Shift]) = 0) "
            "THEN SUM([Sales In Month]) END"
        ),
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "LABEL:First Last if not max or min",
        "formula": (
            "IF FIRST() = 0 THEN SUM([Sales In Month]) "
            "ELSEIF LAST() = 0 THEN "
            "IF NOT(LOOKUP([Is Min Value?], -1)) "
            "AND NOT(LOOKUP([Is Max Value?], -1)) "
            "THEN SUM([Sales In Month]) END END"
        ),
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Sales in Month Dual Axis",
        "formula": (
            "IF [Sales Diff] <> 0 THEN SUM([Sales In Month]) END"
        ),
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Sales Next Value Dual Axis",
        "formula": "IF [Sales Diff] <> 0 THEN [Sales Next Value] END",
        "datatype": "real",
        "table_calc": "Rows",
    },
    {
        "name": "Colour:Diff",
        "formula": (
            "IF [Is Max Value?] THEN 'blue' "
            "ELSEIF [Is Min Value?] THEN 'red' ELSE 'grey' END"
        ),
        "datatype": "string",
        "role": "measure",
        "field_type": "nominal",
        "table_calc": "Rows",
    },
    {
        "name": "Size - Dual Axis",
        "formula": (
            "IF [Colour:Diff] = 'blue' OR [Colour:Diff] = 'red' "
            "THEN 2 ELSE 1 END"
        ),
        "datatype": "integer",
        "table_calc": "Rows",
    },
    {
        "name": "Month Position To Plot",
        "formula": (
            "DATE(IF [Month] = 12 THEN DATETRUNC('month', [Order Date]) "
            "ELSE IF DAY([Order Date]) <= 15 "
            "THEN DATETRUNC('month', [Order Date]) "
            "ELSE DATEADD('month', 1, DATETRUNC('month', [Order Date])) - 1 "
            "END END)"
        ),
        "datatype": "date",
        "role": "dimension",
        "field_type": "quantitative",
    },
    {
        "name": "LABEL:Month Position To Display",
        "formula": (
            "IF MONTH([Month Position To Plot]) = 12 "
            "THEN [Month Position To Plot] "
            "ELSE IF DAY([Month Position To Plot]) = 1 "
            "THEN [Month Position To Plot] "
            "ELSE DATE(DATEADD('day', 1, [Month Position To Plot])) "
            "END END"
        ),
        "datatype": "date",
        "role": "dimension",
        "field_type": "quantitative",
    },
    {
        "name": "LABEL:Sales Diff",
        "formula": (
            "IF ([Sales Next Value] - SUM([Sales In Month])) = 0 "
            "THEN LOOKUP([Sales Next Value], -1) "
            "- LOOKUP(SUM([Sales In Month]), -1) "
            "ELSE [Sales Next Value] - SUM([Sales In Month]) END"
        ),
        "datatype": "real",
        "table_calc": "Rows",
    },
]


LABELS = [
    "LABEL: Max Diff + Shift",
    "LABEL: Min Diff + Shift",
    "LABEL:Sales in Month Max",
    "LABEL:Sales in Month Min",
    "LABEL:First Last if not max or min",
]

TOOLTIPS = [
    "Category",
    "LABEL:Month Position To Display",
    "SUM(Sales In Month)",
    "LABEL:Sales Diff",
    "Sales Next Value",
]

MONTH_ADDRESS = "DAYTRUNC(Month Position To Plot)"
EXTREMA_TABLE_CALCS = {
    "Colour:Diff": [
        {"ordering_type": "Rows"},
        {"field": "Is Max Value?", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {"field": "Is Min Value?", "ordering_type": "Rows"},
        {
            "field": "Max Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {
            "field": "Min Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
    ],
    "Size - Dual Axis": [
        {"ordering_type": "Rows"},
        {"field": "Colour:Diff", "ordering_type": "Rows"},
        {"field": "Is Max Value?", "ordering_type": "Rows"},
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {"field": "Sales Next Value", "ordering_type": "Rows"},
        {"field": "Max Diff", "ordering_type": "Rows"},
        {"field": "Is Min Value?", "ordering_type": "Rows"},
        {"field": "Min Diff", "ordering_type": "Rows"},
    ],
}
LABEL_TABLE_CALCS = {
    "LABEL: Max Diff + Shift": [
        {"ordering_field": MONTH_ADDRESS, "ordering_type": "Field"},
        {"field": "LABEL: Max Diff", "ordering_type": "Rows"},
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Is Max Value?", "ordering_type": "Rows"},
        {
            "field": "Max Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
    ],
    "LABEL:Sales in Month Max": [
        {"ordering_type": "Rows"},
        {
            "field": "LABEL: Max Diff + Shift",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "LABEL: Max Diff", "ordering_type": "Rows"},
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Is Max Value?", "ordering_type": "Rows"},
        {
            "field": "Max Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
    ],
    "LABEL: Min Diff + Shift": [
        {"ordering_field": MONTH_ADDRESS, "ordering_type": "Field"},
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "LABEL: Min Diff", "ordering_type": "Rows"},
        {"field": "Is Min Value?", "ordering_type": "Rows"},
        {
            "field": "Min Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
    ],
    "LABEL:Sales in Month Min": [
        {"ordering_type": "Rows"},
        {"field": "Is Min Value?", "ordering_type": "Rows"},
        {
            "field": "LABEL: Min Diff + Shift",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "LABEL: Min Diff", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {
            "field": "Min Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
    ],
    "LABEL:First Last if not max or min": [
        {"ordering_field": MONTH_ADDRESS, "ordering_type": "Field"},
        {
            "field": "Max Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Is Min Value?", "ordering_type": "Rows"},
        {
            "field": "Sales Next Value",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Sales Diff", "ordering_type": "Rows"},
        {
            "field": "Min Diff",
            "ordering_field": MONTH_ADDRESS,
            "ordering_type": "Field",
        },
        {"field": "Is Max Value?", "ordering_type": "Rows"},
    ],
}


def create_editor(
    *,
    include_extrema: bool = True,
    include_labels: bool = True,
) -> TWBEditor:
    """Create the complete workbook without reading an author TWB/TWBX."""
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER), table_name="Extract")
    month_position_internal = "[WW32_Month_Position_To_Plot]"

    for calculation in CALCULATIONS:
        definition = dict(calculation)
        definition["field_name"] = definition.pop("name")
        definition["internal_name"] = (
            "[WW32_"
            + re.sub(r"[^A-Za-z0-9]+", "_", definition["field_name"]).strip("_")
            + "]"
        )
        if definition["field_name"] == "Month Position To Plot":
            definition["internal_name"] = month_position_internal
        if definition["datatype"] == "real":
            definition["default_format"] = 'c"$"#,##0;("$"#,##0)'
        editor.add_calculated_field(**definition)

    editor.add_worksheet("Viz")
    panes = [
        {
            "mark_type": "Area",
            "selection_relaxation": "selection-relaxation-disallow",
            "mark_style": {
                "mark-labels-show": "false",
                "mark-transparency": "196",
            },
        },
        {
            "mark_type": "Area",
            "axis": "SUM(Sales In Month)",
            "color": "Category",
            "color_map": {
                "Furniture": "#d2deed",
                "Office Supplies": "#caeeea",
                "Technology": "#fadbec",
            },
            "selection_relaxation": "selection-relaxation-disallow",
            "mark_style": {
                "mark-labels-show": "false",
                "mark-transparency": "196",
            },
        },
        {
            "mark_type": "Line",
            "axis": "Multiple Values",
            "measure_values": [
                "Sales in Month Dual Axis",
                "Sales Next Value Dual Axis",
            ],
            "mark_sizing_off": True,
            "selection_relaxation": "selection-relaxation-disallow",
            "mark_style": {
                "mark-labels-show": "false",
                "mark-transparency": "196",
                "size": "0.27484098076820374",
            },
        },
    ]
    if include_extrema:
        panes[2]["color"] = "Colour:Diff"
        panes[2]["color_map"] = {
            "blue": "#4e79a7",
            "red": "#e15759",
            "grey": "#bab0ac",
        }
        panes[2]["size"] = "Size - Dual Axis"
    if include_labels:
        for pane in panes:
            pane["labels"] = LABELS
            pane["tooltip"] = TOOLTIPS
            pane["label_runs"] = [
                {"field": "LABEL:Sales in Month Max", "fontcolor": "#666666", "fontsize": 8},
                {"field": "LABEL:Sales in Month Min", "fontcolor": "#666666", "fontsize": 8},
                {"field": "LABEL:First Last if not max or min", "fontcolor": "#666666", "fontsize": 8},
                {"text": "\u00c6\n"},
                {"field": "LABEL: Min Diff + Shift", "bold": True, "fontcolor": "#da020e", "fontsize": 8},
                {"field": "LABEL: Max Diff + Shift", "bold": True, "fontcolor": "#305d8a", "fontsize": 8},
                {"text": "\u00c6\n"},
            ]
            pane["mark_style"]["mark-labels-show"] = "true"
            pane["mark_style"]["mark-labels-cull"] = "false"

    table_calc_overrides = {}
    if include_extrema:
        table_calc_overrides.update(EXTREMA_TABLE_CALCS)
    if include_labels:
        table_calc_overrides.update(LABEL_TABLE_CALCS)

    editor.configure_layered_chart(
        "Viz",
        columns=["Category", "DAYTRUNC(Month Position To Plot)"],
        rows=["SUM(Sales In Month)", "Multiple Values"],
        panes=panes,
        synchronized=True,
        hide_axes=True,
        table_calc_overrides=table_calc_overrides or None,
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_gridlines=False,
        hide_zeroline=True,
        hide_borders=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_table_dividers=True,
        pane_datalabel_style={"font-size": "8", "color": "#898989"},
        axis_style={"per_field": [{"attr": "line-visibility", "scope": "cols", "value": "on"}, {"attr": "line-pattern-only", "scope": "cols", "value": "solid"}, {"attr": "stroke-size", "scope": "cols", "value": "2"}, {"attr": "stroke-color", "scope": "cols", "value": "#666666"}, {"field": "DAYTRUNC(Month Position To Plot)", "attr": "title", "scope": "cols", "class": "0", "value": ""}, {"field": "DAYTRUNC(Month Position To Plot)", "attr": "stroke-size", "scope": "cols", "value": "2"}, {"field": "DAYTRUNC(Month Position To Plot)", "attr": "stroke-color", "scope": "cols", "value": "#666666"}], "encodings": [{"field": "DAYTRUNC(Month Position To Plot)", "scope": "cols", "class": "0", "range_type": "fixed", "min": "#2017-12-01 00:00:00#", "max": "#2019-01-15 00:00:00#", "major_origin": "#2018-01-01 00:00:00#", "major_spacing": "11.0", "major_units": "months", "minor_show": False}]},
        label_formats=[{"field": "DAYTRUNC(Month Position To Plot)", "text-format": "*mmm yy", "font-size": "8"}],
    )
    if include_extrema:
        editor.set_datasource_color_palette("Colour:Diff", {"blue": "#4e79a7", "red": "#e15759", "grey": "#bab0ac"})
    editor.set_worksheet_rich_title("Viz", runs=[
        {"text": "WHEN DID 2018 CATEGORY SALES ", "fontsize": 16, "fontcolor": "#898989"},
        {"text": "DROP", "fontsize": 16, "fontcolor": "#e15759", "bold": True},
        {"text": " AND ", "fontsize": 16, "fontcolor": "#898989"},
        {"text": "RISE", "fontsize": 16, "fontcolor": "#4e79a7", "bold": True},
        {"text": " THE MOST?", "fontsize": 16, "fontcolor": "#898989"},
    ])
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=600,
        worksheet_names=["Viz"],
        layout={"type": "container", "direction": "vertical", "children": [
            {"type": "worksheet", "name": "Viz", "fit": "entire", "weight": 1},
            {"type": "text", "text": "DESIGNED BY: KLAUS SCHULTE                         #WORKOUTWEDNESDAY | 2019 | WEEK 32                         RECREATED BY: DONNA COLES", "font_size": "8", "font_color": "#4e79a7", "fixed_size": 30},
            {"type": "text", "text": "http://www.workout-wednesday.com/week-32-can-you-create-step-area-charts/", "font_size": "8", "font_color": "#4e79a7", "fixed_size": 25},
        ]},
    )
    return editor


def build(output_path: Path) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_editor().save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    if not HYPER.exists():
        raise FileNotFoundError(f"Locked case Hyper is missing: {HYPER}")
    for filename in ("2019-08-09-ww32-step-area-chart-replicated-workbook.twb", "replicated-workbook.twbx"):
        print(build(OUTPUT_DIR / filename))
