"""Rebuild the WW30 "Let's go streaking!" consecutive-increase dashboard.

The challenge (Sean Miller, built by Donna Coles) asks for the longest run of
consecutive months where monthly sales rose, per Sub-Category, and for the
sales value in the month that closes that run.

Chain:
  data (Order Date, Sub-Category, Sales)
  → Order Date Month = DATE(DATETRUNC('month',[Order Date]))
  → Sales Diff = ZN(SUM([Sales])) - LOOKUP(ZN(SUM([Sales])),-1)
  → Diff Is +ve = IF [Sales Diff]>0 THEN 1 ELSE 0 END
  → Match Prev Value = LOOKUP([Diff Is +ve],-1) = [Diff Is +ve]
  → Increase Streak = recursive PREVIOUS_VALUE accumulation of +ve months
  → Longest Streak = WINDOW_MAX([Increase Streak])
  → Sales of Month with Longest Streak = IF longest = streak THEN SUM([Sales]) END
  → Sort = [Longest Streak] * -1 (discrete, hidden, leading)
  → Viz: stepped grey line (SUM(Sales)) and a coloured circle pane
    (Sales of Month with Longest Streak) folded on a synchronised row axis,
    months on Columns, Sub-Category rows sorted by the hidden Sort pill
  → Legend sheet: CASE-ordered Sub-Category squares on the same green palette
  → dashboard: title, Chart, Legend, challenge/recreation credit strips

Every table calculation is addressed by Order Date Month only, which is what
makes the streak restart per Sub-Category row.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/Orders (Sample - Superstore).hyper"
DASHBOARD = "2021_07_28_WW30_LetsGoStreaking"

# Author palette: a 5-step green ramp from near-white to dark green.
GREEN_RAMP = ["#e8f4e4", "#b7ddb0", "#7fc177", "#4c9b45", "#1f5c1a"]
LINE_GREY = "#898989"
TITLE_GREEN = "#5ea654"

# Field-level metadata names the bucket by its bracketed field name (the
# precedent set by the WW26 case, which Desktop accepts). Chart-level overrides
# below resolve to the exact-date column instance Tableau writes itself.
MONTH_ADDRESS = {
    "ordering_type": "Field",
    "ordering_field": "[Order Date Month]",
}
# The author's month pill is Month-Trunc of the raw date ([tmn:Order Date:qk]),
# a native derivation the SDK resolves directly. Wrapping the calculated
# Order Date Month in EXACTDATE produces an instance Tableau cannot bind, which
# renders every sheet empty.
MONTH_INSTANCE = {
    "ordering_type": "Field",
    "ordering_field": "MONTHTRUNC(Order Date)",
}

SALES_DIFF = "ZN(SUM([Sales])) - LOOKUP(ZN(SUM([Sales])), -1)"
DIFF_POSITIVE = "IF [Sales Diff] > 0 THEN 1 ELSE 0 END"
MATCH_PREV = "LOOKUP([Diff Is +ve], -1) = [Diff Is +ve]"
INCREASE_STREAK = (
    "IF (NOT([Match Prev Value])) AND ([Diff Is +ve] = 1) THEN 1\n"
    "ELSEIF [Diff Is +ve] = 1 THEN ([Diff Is +ve] + PREVIOUS_VALUE([Diff Is +ve]))\n"
    "END"
)
LONGEST_STREAK = "WINDOW_MAX([Increase Streak])"
PEAK_SALES = "IF [Longest Streak] = [Increase Streak] THEN SUM([Sales]) END"
SORT = "[Longest Streak] * -1"
LEGEND = (
    "CASE [Sub-Category]\n"
    "WHEN 'Art' THEN 0\n"
    "WHEN 'Chairs' THEN 1\n"
    "WHEN 'Labels' THEN 2\n"
    "WHEN 'Paper' THEN 3\n"
    "WHEN 'Phones' THEN 4\n"
    "ELSE 5 END"
)

# The four top-ranked Sub-Categories the article's screenshots show first
# (Appliances 5, Bookcases 5, Phones 5, Art 4) all come from the sort field;
# nothing is hard-coded, but the legend order below is the author's CASE.
TOOLTIP_RUNS = [
    {"field": "Sub-Category", "bold": True, "fontsize": 9},
    {"text": " had total sales of ", "fontsize": 9},
    {"field": "SUM(Sales)", "bold": True, "fontsize": 9},
    {"text": " in ", "fontsize": 9},
    # A custom-tooltip run must reference the bare date field: pointing a run at
    # EXACTDATE(<date field>) makes Tableau Cloud render the whole worksheet
    # empty (batch-17 finding, ww20/ww28). The text then shows the month
    # granularity instead of the exact date, which is a text-only difference.
    {"field": "Order Date Month", "bold": True, "fontsize": 9},
]


def add_fields(editor: TWBEditor) -> None:
    """Add the month bucket and the table-calc chain in dependency order."""

    editor.add_calculated_field(
        "Order Date Month",
        "DATE(DATETRUNC('month', [Order Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Sales Diff",
        SALES_DIFF,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
        table_calc=MONTH_ADDRESS,
    )
    editor.add_calculated_field(
        "Diff Is +ve",
        DIFF_POSITIVE,
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=MONTH_ADDRESS,
    )
    editor.add_calculated_field(
        "Match Prev Value",
        MATCH_PREV,
        datatype="boolean",
        role="measure",
        field_type="nominal",
        table_calc=MONTH_ADDRESS,
    )
    editor.add_calculated_field(
        "Increase Streak",
        INCREASE_STREAK,
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=MONTH_ADDRESS,
    )
    editor.add_calculated_field(
        "Longest Streak",
        LONGEST_STREAK,
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=MONTH_ADDRESS,
    )
    # The author keeps two column instances of Longest Streak: a continuous one
    # for the colour ramp and a discrete one for the blue pill on Rows.
    editor.add_calculated_field(
        "Longest Streak (label)",
        "[Longest Streak]",
        datatype="integer",
        role="measure",
        field_type="ordinal",
        table_calc=MONTH_ADDRESS,
    )
    editor.add_calculated_field(
        "Sales of Month with Longest Streak",
        PEAK_SALES,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0;-"$"#,##0',
        table_calc=MONTH_ADDRESS,
    )
    # Sort is the author's hidden *discrete* blue pill in front of Sub-Category;
    # as a continuous pill it would create an extra axis instead of nesting.
    editor.add_calculated_field(
        "Sort",
        SORT,
        datatype="integer",
        role="measure",
        field_type="ordinal",
        table_calc=MONTH_ADDRESS,
    )
    # The author's Legend sheet uses two instances of the same field: a
    # discrete ordinal one for the header row and a quantitative one for the
    # interpolated colour ramp.
    editor.add_calculated_field(
        "Legend",
        LEGEND,
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Legend Colour",
        "[Legend]",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )


def build_chart(editor: TWBEditor) -> None:
    """Stepped sales line plus the streak-closing circle, folded on one axis."""

    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=["MONTHTRUNC(Order Date)"],
        # Discrete pills first, then the measure group, so the builder's
        # nested shelf text is ((Sort / (Sub / Longest)) * (Sales + Peak)) —
        # the author's own shape. A quantitative Sort pill would emit an extra
        # axis instead of nesting under Sub-Category.
        rows=[
            "Sort",
            "Sub-Category",
            "Longest Streak (label)",
            "SUM(Sales)",
            "Sales of Month with Longest Streak",
        ],
        axis_shelf="rows",
        fold_axes=True,
        synchronized=True,
        sort_field="Sub-Category",
        sort_descending="Sort",
        sort_mode="computed",
        panes=[
            {
                "axis": "SUM(Sales)",
                "mark_type": "Line",
                "tooltip": [],
                "mark_style": {
                    "mark-color": LINE_GREY,
                    "line-interpolation": "step",
                    "size": "0.32",
                },
                "mark_sizing_off": True,
            },
            {
                "axis": "Sales of Month with Longest Streak",
                "mark_type": "Circle",
                "color": "Longest Streak",
                "tooltip": [],
                "mark_style": {
                    "line-interpolation": "step",
                    "size": "2.15",
                },
                "mark_sizing_off": True,
            },
        ],
        table_calc_overrides={
            "SUM(Sales)": [MONTH_INSTANCE],
            "Longest Streak (label)": [MONTH_INSTANCE],
            "Sales of Month with Longest Streak": [MONTH_INSTANCE],
            "Longest Streak": [MONTH_INSTANCE],
        },
    )
    # The circle pane carries Longest Streak as a continuous colour ramp that
    # the author pins to the fixed domain 0..5 in five stepped buckets.
    editor.configure_worksheet_style(
        "Chart",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_zeroline=True,
        hide_gridlines=True,
        color_style={
            "field": "Longest Streak",
            "colors": GREEN_RAMP,
            "min": 0,
            "max": 5,
            "num_steps": 5,
        },
        header_formats=[
            {"field": "Sub-Category", "width": 100},
            {"field": "Longest Streak (label)", "width": 60},
        ],
        cell_formats=[
            {"field": "Sub-Category", "height": 48},
        ],
        pane_cell_style={"font-size": "8"},
        label_formats=[
            {"field": "SUM(Sales)", "text-format": 'c"$"#,##0;-"$"#,##0'},
        ],
        axis_style={
            "per_field": [
                {"field": "SUM(Sales)", "scope": "rows", "attr": "title", "value": ""},
                {
                    "field": "MONTHTRUNC(Order Date)",
                    "scope": "cols",
                    "attr": "title",
                    "value": "",
                },
            ]
        },
    )
    for pane_index in (0, 1):
        editor.configure_custom_tooltip("Chart", TOOLTIP_RUNS, pane_index=pane_index)


DATA_MEASURES = [
    "SUM(Sales)",
    "Sales Diff",
    "Diff Is +ve",
    "Increase Streak",
    "Longest Streak",
    "Sales of Month with Longest Streak",
]


def build_data_sheet(editor: TWBEditor) -> None:
    """The author's audit table: one column per link of the streak chain.

    It is deliberately not placed on the dashboard; it exists so the chain can
    be read (and exported) row by row, exactly as the article builds it.
    """

    editor.add_worksheet("Data")
    editor.configure_chart(
        "Data",
        mark_type="Text",
        rows=["Sub-Category", "MONTHTRUNC(Order Date)"],
        measure_values=DATA_MEASURES,
        tooltip=[],
    )
    editor.configure_worksheet_style(
        "Data",
        hide_col_field_labels=True,
        pane_cell_style={"font-size": "8"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        header_formats=[{"field": "Sub-Category", "width": 100}],
    )


def build_legend(editor: TWBEditor) -> None:
    """A separate sheet that renders the author's five-step streak legend."""

    editor.add_worksheet("Legend")
    editor.configure_layered_chart(
        "Legend",
        columns=["Legend"],
        axis_shelf="columns",
        fold_axes=False,
        panes=[
            {
                "axis": "Legend Colour",
                "mark_type": "Square",
                "color": "Legend Colour",
                "label": "Legend",
                "tooltip": [],
                "mark_style": {"shape": ":filled/square"},
                "mark_sizing_off": True,
            }
        ],
    )
    editor.configure_worksheet_style(
        "Legend",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        color_style={
            "field": "Legend Colour",
            "colors": GREEN_RAMP,
            "min": 0,
            "max": 5,
            "num_steps": 5,
        },
        pane_cell_style={"height": "32"},
        pane_datalabel_style={"font-size": "8"},
    )
    editor.set_worksheet_title("Legend", "Streaks")


def build_dashboard(editor: TWBEditor) -> None:
    def pos(x: int, y: int, w: int, h: int) -> dict:
        return {
            "x": round(x / 1366 * 100000),
            "y": round(y / 768 * 100000),
            "w": round(w / 1366 * 100000),
            "h": round(h / 768 * 100000),
        }

    editor.add_dashboard(
        DASHBOARD,
        width=1366,
        height=768,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "Let's go streaking!",
                            "font_size": 22,
                            "font_color": TITLE_GREEN,
                            "fontalignment": 1,
                        }
                    ],
                    "absolute": pos(8, 8, 1350, 52),
                },
                {
                    "type": "worksheet",
                    "name": "Chart",
                    "show_title": False,
                    "fit": "entire",
                    "absolute": pos(8, 60, 1200, 632),
                },
                {
                    "type": "worksheet",
                    "name": "Legend",
                    "show_title": True,
                    "fit": "entire",
                    "absolute": pos(1216, 14, 142, 62),
                },
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "CHALLENGE BY : SEAN MILLER",
                            "font_size": 8,
                            "font_color": TITLE_GREEN,
                        }
                    ],
                    "absolute": pos(8, 698, 450, 30),
                },
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "#WOW2021  |  WEEK 30",
                            "font_size": 8,
                            "font_color": TITLE_GREEN,
                            "fontalignment": 1,
                        }
                    ],
                    "absolute": pos(458, 698, 450, 30),
                },
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "RECREATED BY : DONNA COLES",
                            "font_size": 8,
                            "font_color": TITLE_GREEN,
                            "fontalignment": 2,
                        }
                    ],
                    "absolute": pos(908, 698, 450, 30),
                },
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "http://www.workout-wednesday.com/2021w30tab/",
                            "font_size": 8,
                            "fontalignment": 1,
                        }
                    ],
                    "absolute": pos(8, 730, 1350, 30),
                },
            ],
        },
        worksheet_names=["Chart", "Legend"],
    )
    editor.set_window_state("Chart", hidden=False, zoom_entire_view=True)
    editor.set_window_state("Data", hidden=False, zoom_entire_view=True)
    editor.set_window_state("Legend", hidden=False, zoom_entire_view=True)


def build() -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    add_fields(editor)
    build_chart(editor)
    build_data_sheet(editor)
    build_legend(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
