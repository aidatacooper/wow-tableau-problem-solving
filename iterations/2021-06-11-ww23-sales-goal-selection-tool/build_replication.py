"""Rebuild the WW23 "Sales Goal Selection Tool" dashboard.

The challenge (Ann Jackson, rebuilt by Donna Coles) asks for a goal that can be
switched per sub-category: either "same pace" (this year's average sales per day
extrapolated to the whole year) or "last year + X%". A set action toggles the
sub-categories between the two goal methods and the totals aggregate the mixed
values up into the BANs.

Chain:
  data (Order Date, Category, Sub-Category, Sales)
  → pToday (#2021-06-09#) and pPercentIncrease (0.1)
  → # Days So Far This Year / # Days In Year (DATEDIFF based, leap-year safe)
  → SALES YTD by Sub Cat / SALES LY YTD by Sub Cat / SALES LY
  → Same Pace Goal and LY + Percent Increase Goal
  → "Use Last Year With Increase" set + YEAR-END GOAL Per Sub Cat
    (IF ATTR([Use Last Year With Increase]) THEN LY+pct ELSE Same Pace END)
  → Value to Goal, % of Goal
  → BANs: WINDOW_SUM of the three headline measures, INDEX()=1 keeps every row
    in the window while showing a single row
  → Chart: Measure Values bars (SALES YTD / SALES LY YTD) plus a Gantt goal
    line and MIN(0) text/circle panes on a shared column axis
  → dashboard: two set actions (click a circle adds the sub-category to the
    set, "TOGGLE TYPE" removes it again)
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/TEMP_15y4ojb1ek80451dcvfe90xwheay.hyper"
DASHBOARD = "2021_06_09_WW23_Sales_Goal_Selection"

SALES_YTD_COLOR = "#f2a63b"
SALES_LY_COLOR = "#d3d3d3"
SAME_PACE_COLOR = "#91dcea"
LAST_YEAR_COLOR = "#a4a4d5"
GOAL_COLOR = "#000000"

# The author's initial set membership (image-22 / the workbook's <group>).
INITIAL_SET = ["Accessories", "Copiers", "Machines", "Phones"]

SALES_YTD_BY_SUBCAT = (
    "IF YEAR([Order Date]) = YEAR([pToday]) AND [Order Date] <= [pToday] "
    "THEN [Sales] END"
)
SALES_LY_YTD_BY_SUBCAT = (
    "IF YEAR([Order Date]) = YEAR([pToday])-1 AND [Order Date] <= "
    "DATEADD('year',-1,[pToday]) THEN [Sales] END"
)
SALES_LY = "IF YEAR([Order Date]) = YEAR([pToday])-1 THEN [Sales] END"
DAYS_SO_FAR = (
    "DATEDIFF('day',DATETRUNC('year',[pToday]), [pToday] ) +1"
)
DAYS_IN_YEAR = (
    "DATEDIFF('day',DATETRUNC('year',[pToday]), "
    "DATEADD('year',1,DATETRUNC('year',[pToday])))"
)
SAME_PACE = (
    "(SUM([SALES YTD by Sub Cat])/[# Days So Far This Year]) "
    "* [# Days In Year]"
)
LY_PLUS_PCT = "SUM([SALES LY])*(1+[pPercentIncrease])"
YEAR_END_GOAL = (
    "IF ATTR([Use Last Year With Increase]) then [LY + Percent Increase Goal] "
    "ELSE [Same Pace Goal] END"
)
VALUE_TO_GOAL = "[YEAR-END GOAL Per Sub Cat]-SUM([SALES YTD by Sub Cat])"
PCT_OF_GOAL = "SUM([SALES YTD by Sub Cat])/[YEAR-END GOAL Per Sub Cat]"

MONEY = 'c"$"#,##0;-"$"#,##0'
PERCENT = "p0%"

TOOLTIP_BARS = [
    "SALES YTD by Sub Cat",
    "SALES LY YTD by Sub Cat",
    "YEAR-END GOAL Per Sub Cat",
]

ROW_ADDRESSING = {"ordering_type": "Field", "ordering_field": "[Sub-Category]"}


def add_measures(editor: TWBEditor) -> None:
    """Parameters plus the goal-methodology calculation chain."""
    editor.add_parameter(
        "pToday",
        datatype="date",
        default_value="#2021-06-09#",
        domain_type="any",
    )
    editor.add_parameter(
        "pPercentIncrease",
        datatype="real",
        default_value="0.1",
        domain_type="any",
        default_format=PERCENT,
    )

    editor.add_calculated_field(
        "# Days So Far This Year",
        DAYS_SO_FAR,
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "# Days In Year",
        DAYS_IN_YEAR,
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "SALES YTD by Sub Cat",
        SALES_YTD_BY_SUBCAT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "SALES LY YTD by Sub Cat",
        SALES_LY_YTD_BY_SUBCAT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "SALES LY",
        SALES_LY,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "Same Pace Goal",
        SAME_PACE,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "LY + Percent Increase Goal",
        LY_PLUS_PCT,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )

    # The set is the toggle target; the author seeds it with the four
    # sub-categories that start on the "last year + %" methodology.
    editor.add_set(
        "Use Last Year With Increase",
        "Sub-Category",
        members=list(INITIAL_SET),
    )
    editor.add_calculated_field(
        "YEAR-END GOAL Per Sub Cat",
        YEAR_END_GOAL,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "Value to Goal",
        VALUE_TO_GOAL,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
    )
    editor.add_calculated_field(
        "% of Goal",
        PCT_OF_GOAL,
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=PERCENT,
    )

    # MIN(0) is the author's invisible "anchor" measure that gives the text and
    # circle panes their own column in the shared axis. Three distinct copies
    # match the three separate columns in the author's workbook.
    for name in ("MIN(0)", "Min(0)", "MIN(0) C"):
        editor.add_calculated_field(
            name,
            "MIN(0)",
            datatype="integer",
            role="measure",
            field_type="quantitative",
        )

    editor.set_field_format("Sales", MONEY)

    # Window totals for the BANs. INDEX()=1 filters the view down to a single
    # row while the window functions still see all 17 sub-categories.
    editor.add_calculated_field(
        "Index",
        "INDEX()",
        datatype="integer",
        role="measure",
        field_type="quantitative",
        table_calc=ROW_ADDRESSING,
    )
    editor.add_calculated_field(
        "SALES YTD",
        "WINDOW_SUM(SUM([SALES YTD by Sub Cat]))",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
        table_calc=ROW_ADDRESSING,
    )
    editor.add_calculated_field(
        "SALES LY YTD",
        "WINDOW_SUM(SUM([SALES LY YTD by Sub Cat]))",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
        table_calc=ROW_ADDRESSING,
    )
    editor.add_calculated_field(
        "YEAR-END GOAL",
        "WINDOW_SUM([YEAR-END GOAL Per Sub Cat])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format=MONEY,
        table_calc=ROW_ADDRESSING,
    )


def build_bans(editor: TWBEditor) -> None:
    """One row of three big numbers: SALES YTD, SALES LY YTD, YEAR-END GOAL."""
    editor.add_worksheet("BANs")
    editor.configure_layered_chart(
        "BANs",
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Automatic",
                "label": "Multiple Values",
                "measure_values": ["SALES YTD", "SALES LY YTD", "YEAR-END GOAL"],
                "detail_extra": ["Sub-Category"],
            }
        ],
        filters=[{"column": "Index", "max": "1"}],
    )
    editor.configure_worksheet_style(
        "BANs",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_band_color=True,
        pane_cell_style={
            "vertical-align": "center",
            "text-align": "center",
            "font-size": "18",
            "font-family": "Tableau Medium",
        },
        table_formats=[{"attr": "line-visibility", "value": "off"}],
    )


def build_chart(editor: TWBEditor) -> None:
    """Measure Values bars + Gantt goal + text/circle panes on one column axis."""
    editor.add_worksheet("Chart")
    editor.configure_layered_chart(
        "Chart",
        columns=[
            "Multiple Values",
            "YEAR-END GOAL Per Sub Cat",
            "Value to Goal",
            "% of Goal",
            "MIN(0)",
        ],
        rows=["Category", "Sub-Category"],
        axis_shelf="columns",
        fold_axes=True,
        synchronized=True,
        panes=[
            {
                "axis": "Multiple Values",
                "mark_type": "Bar",
                "color": "Measure Names",
                "size": "Measure Names",
                "tooltip": TOOLTIP_BARS,
                "measure_values": ["SALES YTD by Sub Cat", "SALES LY YTD by Sub Cat"],
                "color_map": {
                    "SALES YTD by Sub Cat": SALES_YTD_COLOR,
                    "SALES LY YTD by Sub Cat": SALES_LY_COLOR,
                },
                "mark_style": {"has-stroke": "true", "stroke-color": "#f5f5f5"},
            },
            {
                "axis": "YEAR-END GOAL Per Sub Cat",
                "mark_type": "GanttBar",
                "tooltip": ["SALES YTD by Sub Cat", "SALES LY YTD by Sub Cat"],
                "detail_extra": ["YEAR-END GOAL Per Sub Cat"],
                "mark_style": {"mark-color": GOAL_COLOR},
            },
            {
                "axis": "Value to Goal",
                "mark_type": "Text",
                "label": "Value to Goal",
                "label_runs": [
                    {"field": "Value to Goal", "fontcolor": "#000000"},
                    {"text": " to goal"},
                ],
                "detail_extra": ["YEAR-END GOAL Per Sub Cat"],
                "tooltip": ["Value to Goal"],
            },
            {
                "axis": "% of Goal",
                "mark_type": "Text",
                "label": "% of Goal",
                "label_runs": [
                    {"field": "% of Goal", "fontcolor": "#000000"},
                    {"text": " of goal"},
                ],
                "detail_extra": ["YEAR-END GOAL Per Sub Cat"],
                "tooltip": ["% of Goal"],
            },
            {
                "axis": "MIN(0)",
                "mark_type": "Circle",
                "color": "Use Last Year With Increase",
                "detail_extra": ["YEAR-END GOAL Per Sub Cat"],
                "tooltip": ["Use Last Year With Increase"],
                "color_map": {"false": SAME_PACE_COLOR, "true": LAST_YEAR_COLOR},
                "mark_style": {"size": "1.5"},
            },
        ],
    )
    editor.configure_worksheet_style(
        "Chart",
        hide_gridlines=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_band_color=True,
        hide_table_dividers=True,
        pane_cell_style={"font-size": "10", "text-align": "right"},
        header_formats=[{"field": "Category", "width": "40"}],
        label_formats=[
            {"field": "Category", "text-orientation": "-90"},
            {"field": "Category", "font-weight": "bold"},
            {"field": "Category", "font-size": "11"},
            {"field": "Sub-Category", "font-size": "10"},
            {"field": "Sub-Category", "font-family": "Tableau Book"},
        ],
        table_formats=[
            {"attr": "line-visibility", "value": "off"},
            {"attr": "band-size", "scope": "rows", "value": "1"},
            {"attr": "band-level", "scope": "rows", "value": "1"},
        ],
    )

def build_dashboard(editor: TWBEditor) -> None:
    """Title band, BAN strip and the chart, plus the two set actions."""

    def pos(x, y, w, h):
        return {
            "x": round(x / 1200 * 100000),
            "y": round(y / 800 * 100000),
            "w": round(w / 1200 * 100000),
            "h": round(h / 800 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "SALES GOAL SELECTION TOOL",
                    "font_size": 18,
                    "font_color": "#333333",
                    "font_alignment": 0,
                },
                {"text": "\u00c6\n"},
                {
                    "text": "CLICK BUTTON TO TOGGLE GOAL CALCULATION",
                    "font_color": "#333333",
                    "font_alignment": 0,
                },
            ],
            "absolute": pos(8, 8, 1184, 60),
        },
        {
            "type": "worksheet",
            "name": "BANs",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 68, 1184, 90),
        },
        {
            "type": "worksheet",
            "name": "Chart",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 158, 1184, 602),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "CHALLENGE BY: ANN JACKSON  |  RECREATED BY : DONNA COLES",
                    "font_size": 8,
                    "font_color": "#9090ba",
                    "bold": True,
                }
            ],
            "absolute": pos(8, 760, 400, 32),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "#WOW2021  |  WEEK 23",
                    "font_size": 8,
                    "font_color": "#9090ba",
                    "bold": True,
                    "font_alignment": 1,
                }
            ],
            "absolute": pos(410, 760, 280, 32),
        },
        {
            "type": "text",
            "runs": [
                {"text": "\u25cf", "font_size": 14, "font_color": LAST_YEAR_COLOR},
                {"text": " LAST YEAR SALES + 10%  |  ", "font_size": 8},
                {"text": "\u25cf", "font_size": 14, "font_color": SAME_PACE_COLOR},
                {"text": " SAME PACE", "font_size": 8},
            ],
            "absolute": pos(700, 760, 492, 32),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=1200,
        height=800,
        layout={"type": "container", "direction": "floating", "children": children},
        worksheet_names=["BANs", "Chart"],
    )

    # Clicking a circle adds that sub-category to the "last year + %" set.
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet="Chart",
        target_set="Use Last Year With Increase",
        event_type="on-select",
        caption="Add to Set",
        clear_option="do-nothing",
        selection_mode="add",
    )
    # The tooltip's action name removes it again, toggling back to same pace.
    editor.add_dashboard_set_action(
        DASHBOARD,
        source_sheet="Chart",
        target_set="Use Last Year With Increase",
        event_type="explicit",
        caption="TOGGLE TYPE",
        clear_option="do-nothing",
        selection_mode="remove",
    )

    for name in ("BANs", "Chart"):
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    add_measures(editor)
    build_bans(editor)
    build_chart(editor)
    build_dashboard(editor)

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
