"""Build WW02 (2022) weekly year-over-year line chart with public cwtwb APIs.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate). Visual constants (palette hexes, axis rules,
date formats, dashboard furniture) mirror the analysis notes in analysis.md.

The whole case rests on three calculated fields that Tableau cannot express in
one step:

* ``Order Date Week Start`` snaps every order date to its Monday, so a "week"
  is one comparable bucket across all three years.
* ``Year Group`` is the *signed year offset from the Today parameter*, not the
  calendar year, so the week that straddles 31 Dec belongs to a single group
  instead of being split by YEAR([Order Date]).
* ``Date to Plot`` re-bases each week start onto the equivalent 2021 date, so
  three years of weekly points share one continuous axis.
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "Sales Growth (2022_01_12_WW01_Superstore Sales Growth).hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2022_01_11_WW02_YoY_By_Week"
WORKSHEET = "Line Chart"
POST_URL = "https://www.workout-wednesday.com/2022w02tab/"

# The challenge fixes "today" so the extract's 2021 tail is not treated as
# incomplete data. 1 Dec 2021 is a Wednesday, so the week 29 Nov - 5 Dec 2021
# is the first incomplete week and must be dropped.
TODAY = "#2021-12-01#"

# Author palettes, keyed by the Year Group offset (0 = current year).
YEAR_GROUP_COLORS = {"0": "#9cbe30", "1": "#a0cbe8", "2": "#bfbfbf"}

# Author mark sizing (marks-scaling-off with an explicit size).
MARK_SIZE = "0.86756908893585205"

# Custom number formats copied from the author workbook.
SALES_FORMAT = 'n"$"#,##0;-"$"#,##0'
DIFF_FORMAT = "*▲0.0%;▼0.0%"

# Tableau titles only break lines on the "Æ\n" paragraph separator (a raw
# newline is dropped); the author writes the same sequence, and the Æ glyph
# renders invisibly. fontalignment="1" centres every run, as in the author's
# title. cwtwb's rich-title writer has no fontname attribute, so the title
# renders in Tableau's default title font instead of Tableau Medium.
TITLE_RUNS = [
    {"text": "CAN YOU BUILD A WEEKLY YEAR-OVER-YEAR LINE CHART?", "fontalignment": "1"},
    {"text": "Æ\n"},
    {"text": "CURRENT", "fontcolor": "#9cbe30", "fontsize": "10", "fontalignment": "1"},
    {"text": "  | ", "fontsize": "10", "fontalignment": "1"},
    {"text": "PREVIOUS", "fontcolor": "#a0cbe8", "fontsize": "10", "fontalignment": "1"},
    {"text": "  | ", "fontsize": "10", "fontalignment": "1"},
    {"text": "2 YRS AGO", "fontcolor": "#bfbfbf", "fontsize": "10", "fontalignment": "1"},
]

# Tooltip layout, matching the author's "Week ending / Period / Sales / YoY%"
# block. The coloured percentage is split into a +ve and a -ve field so the
# sign can carry the author's green/red.
TOOLTIP_RUNS = [
    {"text": "Week ending", "fontname": "Tableau Medium"},
    {"field": "ATTR(Order Date Week End)", "bold": True, "fontname": "Tableau Medium"},
    {"text": "\n"},
    {"text": "Period", "fontname": "Tableau Medium", "fontsize": "8"},
    {"field": "ATTR(Period Label)", "bold": True, "fontname": "Tableau Medium", "fontsize": "8"},
    {"text": "\n"},
    {"text": "\n"},
    {"text": "Sales", "fontname": "Tableau Medium"},
    {"field": "SUM(Sales)", "bold": True, "fontname": "Tableau Medium", "prefix": ": "},
    {"text": "\n"},
    {"field": "TOOLTIP: Label YoY%", "fontname": "Tableau Medium"},
    {"text": " ", "bold": True, "fontname": "Tableau Medium"},
    {"field": "% Sales Diff +ve", "bold": True, "fontcolor": "#9cbe30", "fontname": "Tableau Medium"},
    {"field": "% Sales Diff -ve", "bold": True, "fontcolor": "#e15759", "fontname": "Tableau Medium"},
    {"text": "\n"},
]

# Every table calculation addresses the year groups in view order, so the
# percentage difference compares a week against the *next* year group in that
# order (current -> previous -> 2 yrs ago). `% Sales Diff` is never on a shelf
# on its own: it is reached through the +ve/-ve and label fields, which nest
# its addressing metadata.
#
# The addressing must be the `ordering-field` *attribute* (what Tableau writes
# for "Compute Using: Year Group"), not an `<order>` child. With `<order>`
# Tableau partitions by Year Group and runs the calculation along the date
# axis instead, which silently returns week-over-week growth rather than
# year-over-year growth.
YEAR_GROUP_ADDRESS = [{"ordering_type": "Field", "ordering_field": "Year Group"}]
TABLE_CALC_OVERRIDES = {
    "% Sales Diff +ve": YEAR_GROUP_ADDRESS,
    "% Sales Diff -ve": YEAR_GROUP_ADDRESS,
    "TOOLTIP: Label YoY%": YEAR_GROUP_ADDRESS,
}
TABLE_CALC_FIELDS = {"% Sales Diff", "% Sales Diff +ve", "% Sales Diff -ve", "TOOLTIP: Label YoY%"}


def _field_table_calc(editor, name: str):
    """Return the table-calc metadata stored on a calculated field definition.

    Tableau stores a worksheet's addressing for a *referenced* calculation in
    the nested ``<table-calc field=...>`` metadata of the referencing
    instance, and that metadata is copied from the referenced field's own
    definition. ``% Sales Diff`` therefore has to declare its Year Group
    addressing here: with Tableau's default ``Rows`` addressing the LOOKUP
    walks along the date axis and quietly reports week-over-week growth
    instead of year-over-year growth.
    """
    if name == "% Sales Diff":
        datasource = editor.field_registry.datasource_name
        return {
            "ordering_type": "Field",
            "ordering_field": f"[{datasource}].[Calculation_YearGroup]",
        }
    if name in TABLE_CALC_FIELDS:
        return "Rows"
    return None

CALCULATED_FIELDS = [
    (
        "Order Date Week Start",
        "[Calculation_WeekStart]",
        "DATE(DATETRUNC('week', [Order Date]))",
        "date",
        "dimension",
        "ordinal",
        "",
    ),
    (
        "Order Date Week End",
        "[Calculation_WeekEnd]",
        "DATE(DATEADD('day', 6, [Order Date Week Start]))",
        "date",
        "dimension",
        "ordinal",
        "",
    ),
    (
        # Signed offset from "today", not the calendar year. The week of
        # 30 Dec 2019 - 5 Jan 2020 keeps a single group instead of being split
        # between two calendar years. Ascending member order is therefore
        # Current, Previous, 2 Yrs Ago, which is also the colour/table-calc
        # order the author fixes by hand in Tableau.
        "Year Group",
        "[Calculation_YearGroup]",
        "YEAR([Parameters].[Today]) - YEAR([Order Date Week Start])",
        "integer",
        "dimension",
        "ordinal",
        "",
    ),
    (
        # Re-base onto 2021 so all three years share one continuous axis, then
        # truncate back to the Monday of that week. The truncation is what
        # makes the chart work: MAKEDATE keeps the month/day but not the
        # weekday, so 2019-01-07 / 2020-01-06 / 2021-01-04 land on a Thursday,
        # a Wednesday and a Monday. Only after snapping all three to the same
        # Monday do the year groups share an x position, which is what lets the
        # percentage-difference table calculation compare them at all. The
        # author gets the same grouping from Tableau's continuous week-trunc
        # date pill; cwtwb has no week-trunc derivation, so the truncation is
        # folded into the calculation instead.
        # Declared quantitative so the shelf binds it as a continuous
        # exact-date axis.
        "Date to Plot",
        "[Calculation_DateToPlot]",
        "DATE(DATETRUNC('week', MAKEDATE(2021, MONTH([Order Date Week Start]), "
        "DAY([Order Date Week Start]))))",
        "date",
        "dimension",
        "quantitative",
        "",
    ),
    (
        # Complete weeks only: the week containing "today" is still in flight.
        "Core Data to Include",
        "[Calculation_CoreData]",
        "[Order Date Week End] < [Parameters].[Today] AND "
        "YEAR([Order Date Week Start]) >= YEAR([Parameters].[Today]) - 2",
        "boolean",
        "dimension",
        "nominal",
        "",
    ),
    (
        # The author aliases the Year Group members in Tableau. cwtwb has no
        # dimension member alias primitive, so the same three labels are
        # produced as a string field for the tooltip.
        "Period Label",
        "[Calculation_PeriodLabel]",
        "IF YEAR([Parameters].[Today]) - YEAR([Order Date Week Start]) = 0 THEN 'Current'\n"
        "ELSEIF YEAR([Parameters].[Today]) - YEAR([Order Date Week Start]) = 1 THEN 'Previous'\n"
        "ELSE '2 Yrs Ago' END",
        "string",
        "dimension",
        "nominal",
        "",
    ),
    (
        # The baked equivalent of Tableau's "Percentage Difference" quick table
        # calculation: the previous year group is one step along the Year Group
        # addressing, so LOOKUP(..., 1) reads the prior year's value.
        "% Sales Diff",
        "[Calculation_SalesDiff]",
        "(ZN(SUM([Sales])) - LOOKUP(ZN(SUM([Sales])), 1)) / ABS(LOOKUP(ZN(SUM([Sales])), 1))",
        "real",
        "measure",
        "quantitative",
        "",
    ),
    (
        "% Sales Diff +ve",
        "[Calculation_SalesDiffPos]",
        "IF [% Sales Diff] >= 0 THEN [% Sales Diff] END",
        "real",
        "measure",
        "quantitative",
        DIFF_FORMAT,
    ),
    (
        "% Sales Diff -ve",
        "[Calculation_SalesDiffNeg]",
        "IF [% Sales Diff] < 0 THEN [% Sales Diff] END",
        "real",
        "measure",
        "quantitative",
        DIFF_FORMAT,
    ),
    (
        # The 2 yrs ago line has no percentage difference, so its tooltip must
        # not show the "YoY%:" label either.
        "TOOLTIP: Label YoY%",
        "[Calculation_YoYLabel]",
        "IF NOT(ISNULL([% Sales Diff])) THEN 'YoY%:' END",
        "string",
        "measure",
        "nominal",
        "",
    ),
]


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))
    # The author sets the datasource date property to start weeks on Monday;
    # without it DATETRUNC('week', ...) snaps to Sunday and every bucket shifts.
    editor.set_date_options(start_of_week="monday")
    editor.add_parameter("Today", datatype="date", default_value=TODAY, domain_type="any")

    for name, internal, formula, datatype, role, field_type, default_format in CALCULATED_FIELDS:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format=default_format,
            internal_name=internal,
            table_calc=_field_table_calc(editor, name),
        )

    editor.add_worksheet(WORKSHEET)
    editor.configure_chart(
        WORKSHEET,
        mark_type="Line",
        columns=["EXACTDATE(Date to Plot)"],
        rows=["SUM(Sales)"],
        color="Year Group",
        tooltip=[
            "ATTR(Order Date Week End)",
            "ATTR(Period Label)",
            "% Sales Diff +ve",
            "% Sales Diff -ve",
            "TOOLTIP: Label YoY%",
        ],
        filters=[{"column": "Core Data to Include", "values": [True]}],
        mark_sizing_off=True,
        table_calc_overrides=TABLE_CALC_OVERRIDES,
    )

    editor.set_datasource_color_palette("Year Group", dict(YEAR_GROUP_COLORS))

    editor.configure_worksheet_style(
        WORKSHEET,
        # Author gridline rule: row gridlines off (column gridlines stay at
        # the Tableau default of off).
        gridline_style={"rows": {"stroke-size": "0", "line-visibility": "off"}},
        label_formats=[
            # Continuous axis tick labels as "dd mmm" (10 Jan).
            {"field": "EXACTDATE(Date to Plot)", "text-format": "*dd mmm"},
        ],
        cell_formats=[
            # Tooltip week-ending date as "mmm dd" (Jan 10).
            {"field": "ATTR(Order Date Week End)", "text-format": "*mmm dd"},
        ],
        axis_style={
            "per_field": [
                {"field": "SUM(Sales)", "attr": "title", "value": "", "class": 0, "scope": "rows"},
                {"field": "EXACTDATE(Date to Plot)", "attr": "title", "value": "", "class": 0, "scope": "cols"},
            ]
        },
        panes_style={
            "0": {
                "mark_style": {
                    "mark-labels-show": "false",
                    "size": MARK_SIZE,
                }
            }
        },
    )

    editor.set_field_format("Sales", SALES_FORMAT)

    editor.configure_custom_tooltip(WORKSHEET, runs=TOOLTIP_RUNS)
    editor.set_worksheet_rich_title(WORKSHEET, TITLE_RUNS)

    def _credit(text: str, alignment: str, x: int, width: int) -> dict:
        return {
            "type": "text",
            "runs": [
                {
                    "text": text,
                    "bold": True,
                    "font_size": "8",
                    "font_color": "#9cbe30",
                    "font_name": "Tableau Medium",
                    "font_alignment": alignment,
                }
            ],
            "absolute": {"x": x, "y": 91000, "w": width, "h": 4000},
            "style": {"margin": "4"},
        }

    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"margin": "8"},
        "children": [
            {
                "type": "worksheet",
                "name": WORKSHEET,
                "show_title": True,
                "fit": "entire",
                "absolute": {"x": 727, "y": 1000, "w": 98546, "h": 90000},
                "style": {"margin": "4"},
            },
            _credit("CHALLENGE BY : KYLE YETTER", "0", 727, 32848),
            _credit("#WOW2022  |  WEEK 02", "1", 33575, 32850),
            _credit("RECREATED BY : DONNA COLES", "2", 66425, 32848),
            {
                "type": "text",
                "text": POST_URL,
                "runs": [
                    {
                        "text": POST_URL,
                        "font_size": "8",
                        "bold": True,
                        "font_alignment": "1",
                        "hyperlink": f"tabdoc:load-url url=&quot;{POST_URL}&quot;",
                    }
                ],
                "absolute": {"x": 727, "y": 95000, "w": 98546, "h": 4000},
                "style": {"margin": "4"},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1100,
        height=800,
        layout=layout,
        worksheet_names=[WORKSHEET],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2022-01-14-ww02-can-you-build-a-weekly-year-over-year-line-chart-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
