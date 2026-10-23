"""Rebuild the WW38 "net change between two dates" dashboard.

Challenge set by Will Perkins (inspired by Google's stock tracker), solved by
Donna Coles.  The reader picks a timeframe, then drags across the trend lines to
select a date range; four regional KPI cells report the net change in sales
between the first and last *trading* day inside that range.

Chain:
  data (Order Date, Region, Sales) + a five-row "Date Range" list source
  → pToday / pStartRange / pEndRange / pTimeframe parameters
  → Selected Range Start/End Date (default = the 14 days ending pToday)
  → Order Date Day, Selected Dates to Plot, Timeframe to Display (filter)
  → Min/Max Selected Date Per Region and Min/Max Date Sales (FIXED LoDs)
  → Range Sales Diff / Range Sales % Diff / Colour - KPI / Colour - Trend
  → Trend (folded Line + Area over two date axes, per-pane reference bands
    coloured by the sign of the change)
  → KPI table (Region rows, MIN(0) column, text marks)
  → Subtitle, Timeframe Selector
  → dashboard: timeframe action, two min/max date actions and the two
    True→False "deselect" filter actions
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
ORDERS = HERE / "inputs/Orders (Sample - Superstore).hyper"
DATE_RANGE = HERE / "inputs/Date Range.hyper"
DASHBOARD = "2021_09_22_WW38_Daily_Sales_Tracker"

TIMEFRAMES = ["1 MONTH", "6 MONTHS", "YTD", "1 YEAR", "MAX"]

# Author palette: positive trend teal, negative trend red, out-of-range white;
# KPI text green/red; the two reference bands (negative salmon, positive sage).
POSITIVE_TREND = "#57c4ad"
NEGATIVE_TREND = "#eb4325"
OUT_OF_RANGE = "#ffffff"
KPI_POSITIVE = "#59a14f"
KPI_NEGATIVE = "#e15759"
BAND_NEGATIVE = "#e8a09a"
BAND_POSITIVE = "#f1f5e2"
BACKGROUND = "#000000"

TIMEFRAME_TO_DISPLAY = (
    "CASE [pTimeframe]\n"
    "WHEN '1 MONTH' THEN [Order Date Day]>=DATEADD('month',-1,[pToday]) "
    "AND [Order Date Day]<= [pToday]\n"
    "WHEN '6 MONTHS' THEN [Order Date Day]>=DATEADD('month', -6, [pToday]) "
    "AND [Order Date Day]<= [pToday]\n"
    "WHEN 'YTD' THEN [Order Date Day]>=DATETRUNC('year',[pToday]) "
    "AND [Order Date Day]<= [pToday]\n"
    "WHEN '1 YEAR' THEN [Order Date Day]>= DATEADD('year',-1,[pToday]) "
    "AND [Order Date Day]<= [pToday]\n"
    "ELSE [Order Date Day] <= [pToday]\n"
    "END"
)


def _parameters(editor):
    editor.add_parameter(
        "pToday", datatype="date", default_value="#2021-09-20#", domain_type="any"
    )
    editor.add_parameter(
        "pStartRange",
        datatype="date",
        default_value="#1900-01-01#",
        domain_type="any",
    )
    editor.add_parameter(
        "pEndRange",
        datatype="date",
        default_value="#1900-01-01#",
        domain_type="any",
    )
    editor.add_parameter(
        "pTimeframe",
        datatype="string",
        default_value="6 MONTHS",
        domain_type="list",
        allowed_values=TIMEFRAMES,
    )


def _calculated_fields(editor):
    date_dimension = {"datatype": "date", "role": "dimension", "field_type": "quantitative"}

    editor.add_calculated_field(
        "Selected Range Start Date",
        "IF [pStartRange] = #1900-01-01# THEN DATE(DATEADD('day',-14,[pToday]))\n"
        "ELSE DATE([pStartRange])\nEND",
        **date_dimension,
    )
    editor.add_calculated_field(
        "Selected Range End Date",
        "IF [pEndRange] = #1900-01-01# THEN DATE([pToday])\n"
        "ELSE DATE([pEndRange])\nEND",
        **date_dimension,
    )
    editor.add_calculated_field(
        "Order Date Day",
        "DATE(DATETRUNC('day',[Order Date]))",
        **date_dimension,
    )
    editor.add_calculated_field(
        "Timeframe to Display",
        TIMEFRAME_TO_DISPLAY,
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "Selected Dates to Plot",
        "IF [Order Date Day]>= [Selected Range Start Date] AND "
        "[Order Date Day]<=[Selected Range End Date] THEN [Order Date Day] END",
        **date_dimension,
    )
    # The author resolves the range per region from the days that actually have
    # a sale, so a region with no sale on the exact range boundary still gets a
    # first/last trading day instead of a null.
    editor.add_calculated_field(
        "Min Selected Date Per Region",
        "{FIXED [Region]: MIN([Selected Dates to Plot])}",
        **date_dimension,
    )
    editor.add_calculated_field(
        "Max Selected Date Per Region",
        "{FIXED [Region]: MAX([Selected Dates to Plot])}",
        **date_dimension,
    )
    editor.add_calculated_field(
        "Min Date Sales",
        "{FIXED [Region]: SUM(IF [Order Date Day]=[Min Selected Date Per Region] "
        "THEN [Sales] END)}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0.00;-"$"#,##0.00',
    )
    editor.add_calculated_field(
        "Max Date Sales",
        "{FIXED [Region]: SUM(IF [Order Date Day]=[Max Selected Date Per Region] "
        "THEN [Sales] END)}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='c"$"#,##0.00;-"$"#,##0.00',
    )
    editor.add_calculated_field(
        "Range Sales Diff",
        "SUM([Max Date Sales])-SUM([Min Date Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format='*+"$"#,##0.00;-"$"#,##0.00',
    )
    editor.add_calculated_field(
        "Range Sales % Diff",
        "[Range Sales Diff]/SUM([Min Date Sales])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*▲0.0%;▼0.0%",
    )
    editor.add_calculated_field(
        "Colour - Trend",
        "IF MIN([Order Date Day]) >= [Selected Range Start Date] AND "
        "MIN([Order Date Day])<= [Selected Range End Date] THEN\n"
        "    IF [Range Sales Diff]>= 0 THEN 1\n"
        "    ELSE -1\n"
        "    END\n"
        "ELSE 0\nEND",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    editor.add_calculated_field(
        "Colour - KPI",
        "[Range Sales Diff]>=0",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    # Reference-band endpoints. They stay null for the half of the regions whose
    # change has the other sign, so each band only paints its own rows.
    for caption, condition in (
        ("Ref Line Start Date -ve", "<0"),
        ("Ref Line End Date -ve", "<0"),
        ("Ref Line Start Date +ve", ">=0"),
        ("Ref Line End Date +ve", ">=0"),
    ):
        source = (
            "[Selected Range Start Date]"
            if "Start" in caption
            else "[Selected Range End Date]"
        )
        editor.add_calculated_field(
            caption,
            f"IF [Range Sales Diff]{condition} THEN {source} END",
            datatype="date",
            role="measure",
            field_type="quantitative",
        )
    editor.add_calculated_field(
        "MIN(0)", "MIN(0)", datatype="integer", role="measure",
        field_type="quantitative",
    )
    # Constants for the "deselect" True→False filter actions.
    editor.add_calculated_field(
        "True", "True", datatype="boolean", role="dimension", field_type="nominal"
    )
    editor.add_calculated_field(
        "False", "False", datatype="boolean", role="dimension", field_type="nominal"
    )
    # The author sorts the regions South, West, Central, East. cwtwb exposes
    # native descending computed sorts, so the negated rank reproduces that
    # order without hand-written XML.
    editor.add_calculated_field(
        "Region Rank (desc)",
        "CASE [Region] WHEN 'South' THEN -1 WHEN 'West' THEN -2 "
        "WHEN 'Central' THEN -3 ELSE -4 END",
        datatype="integer",
        role="measure",
        field_type="quantitative",
    )

    editor.set_field_format("Sales", 'c"$"#,##0.00;-"$"#,##0.00')
    editor.set_field_format("Selected Range Start Date", "*mmm dd, yyyy")
    editor.set_field_format("Selected Range End Date", "*MMM dd, yyyy")


def _trend(editor):
    editor.add_worksheet("Trend")
    editor.configure_layered_chart(
        "Trend",
        columns=["[Order Date Day]", "[Selected Dates to Plot]"],
        rows=["Region", "SUM(Sales)"],
        axis_shelf="columns",
        fold_axes=True,
        synchronized=True,
        filters=[{"column": "Timeframe to Display", "values": [True]}],
        sort_field="Region",
        sort_descending="AVG(Region Rank (desc))",
        sort_mode="computed",
        panes=[
            {
                "axis": "[Order Date Day]",
                "mark_type": "Line",
                "breakdown": "off",
                "selection_relaxation": "disallow",
                "color": "Colour - Trend",
                "color_map": {
                    "1": POSITIVE_TREND,
                    "-1": NEGATIVE_TREND,
                    "0": OUT_OF_RANGE,
                },
                "detail_extra": [
                    "True",
                    "False",
                    # The band endpoints must sit on Detail: a per-cell band
                    # whose value field is not in the view resolves to null and
                    # the sheet renders blank.
                    "Ref Line Start Date -ve",
                    "Ref Line End Date -ve",
                ],
                "tooltip": ["[Order Date Day]", "SUM(Sales)"],
                "mark_style": {"size": "0.22988949716091156"},
            },
            {
                "axis": "[Selected Dates to Plot]",
                "mark_type": "Area",
                "breakdown": "off",
                "selection_relaxation": "disallow",
                "color": "Colour - Trend",
                "color_map": {
                    "1": POSITIVE_TREND,
                    "-1": NEGATIVE_TREND,
                    "0": OUT_OF_RANGE,
                },
                "detail_extra": [
                    "True",
                    "False",
                    "Ref Line Start Date -ve",
                    "Ref Line End Date -ve",
                    "Ref Line Start Date +ve",
                    "Ref Line End Date +ve",
                ],
                "tooltip": ["[Selected Dates to Plot]", "SUM(Sales)"],
            },
        ],
    )
    # Both conditional bands belong to the final visible Area pane. Its axis
    # is synchronized with the full-history Line axis. Attaching the negative
    # band to the earlier Line pane leaves its correct query values covered by
    # the later pane background in Cloud, so render both on this final pane.
    for sign, color in (("-ve", BAND_NEGATIVE), ("+ve", BAND_POSITIVE)):
        editor.add_reference_band(
            "Trend",
            axis_field="[Selected Dates to Plot]",
            lower_field=f"Ref Line Start Date {sign}",
            upper_field=f"Ref Line End Date {sign}",
            lower_formula="min",
            upper_formula="max",
            scope="per-cell",
            pane_index=1,
            fill_color=color,
        )
    editor.configure_worksheet_style(
        "Trend",
        background_color=BACKGROUND,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=False,
        axis_style={
            "per_field": [
                {
                    "field": "[Order Date Day]",
                    "scope": "cols",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "[Selected Dates to Plot]",
                    "scope": "cols",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "SUM(Sales)",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "[Order Date Day]",
                    "scope": "cols",
                    "attr": "tick-color",
                    "value": "#00000000",
                },
            ]
        },
    )


def _kpi(editor):
    editor.add_worksheet("KPI")
    editor.configure_chart(
        "KPI",
        mark_type="Text",
        columns=["MIN(0)"],
        rows=["Region"],
        color="Colour - KPI",
        color_map={"true": KPI_POSITIVE, "false": KPI_NEGATIVE},
        label="Range Sales Diff",
        label_extra=["Range Sales % Diff"],
        label_runs=[
            {"field": "Range Sales Diff", "fontname": "Tableau Medium",
             "fontsize": 10, "bold": True},
            {"text": "\n"},
            {"field": "Range Sales % Diff", "fontname": "Tableau Medium",
             "fontsize": 8, "bold": True},
        ],
        sort_field="Region",
        sort_descending="AVG(Region Rank (desc))",
        mark_sizing_off=True,
    )
    # Text marks do not route color_map through the datasource palette, so the
    # author's green/red KPI text needs the palette registered explicitly.
    editor.set_datasource_color_palette(
        "Colour - KPI", {"true": KPI_POSITIVE, "false": KPI_NEGATIVE}
    )
    editor.configure_worksheet_style(
        "KPI",
        background_color=BACKGROUND,
        hide_axes=False,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        label_formats=[
            {"field": "Region", "color": "#ffffff", "font-weight": "bold",
             "font-size": "10", "text-align": "left"},
            {"field": "MIN(0)", "display": "false"},
        ],
        cell_formats=[{"field": "Region", "height": "80"}],
        axis_style={
            "per_field": [
                {
                    "field": "MIN(0)",
                    "scope": "cols",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "Region",
                    "scope": "rows",
                    "attr": "display",
                    "value": "true",
                },
            ]
        },
    )


def _subtitle(editor):
    editor.add_worksheet("Subtitle")
    editor.configure_chart(
        "Subtitle",
        mark_type="Text",
        label_extra=[
            "[Selected Range Start Date]",
            "[Selected Range End Date]",
        ],
        label_runs=[
            {"text": "DISPLAYING THE NET CHANGE FROM ", "fontcolor": "#ffffff",
             "fontsize": 10},
            {"field": "[Selected Range Start Date]",
             "fontcolor": "#ffffff", "fontsize": 10},
            {"text": " TO ", "fontcolor": "#ffffff", "fontsize": 10},
            {"field": "[Selected Range End Date]",
             "fontcolor": "#ffffff", "fontsize": 10},
        ],
    )
    editor.configure_worksheet_style(
        "Subtitle",
        background_color=BACKGROUND,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "false"},
    )


def _timeframe_selector(editor):
    editor.add_hyper_datasource("Date Range", str(DATE_RANGE))
    editor.add_calculated_field(
        "Timeframe Selected",
        "[Date Range] = [pTimeframe]",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    editor.add_calculated_field(
        "True", "True", datatype="boolean", role="dimension", field_type="nominal"
    )
    editor.add_calculated_field(
        "False", "False", datatype="boolean", role="dimension", field_type="nominal"
    )
    editor.add_worksheet("Timeframe Selector")
    editor.configure_chart(
        "Timeframe Selector",
        mark_type="Text",
        columns=["Date Range"],
        label="Date Range",
        color="Timeframe Selected",
        size="Timeframe Selected",
        color_map={"true": "#ffffff", "false": "#d5d5d5"},
        detail="True",
        mark_sizing_off=True,
    )
    editor.set_datasource_color_palette(
        "Timeframe Selected", {"true": "#ffffff", "false": "#d5d5d5"}
    )
    editor.configure_worksheet_style(
        "Timeframe Selector",
        background_color=BACKGROUND,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "center", "height": "55"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "true"},
        size_style={
            "field": "Timeframe Selected",
            "type": "catsize",
            "min_size": "0.570131",
            "max_size": "1",
        },
    )


def _dashboard(editor):
    def pos(x, y, w, h):
        """Absolute position on the author's 700 x 500 fixed canvas."""
        return {
            "x": round(x / 700 * 100000),
            "y": round(y / 500 * 100000),
            "w": round(w / 700 * 100000),
            "h": round(h / 500 * 100000),
        }

    children = [
        {
            "type": "text",
            "runs": [
                {"text": "SUPERSTORE DAILY SALES TRACKER", "font_size": "14",
                 "font_color": "#ffffff", "font_name": "Tableau Medium"},
            ],
            "absolute": pos(8, 8, 684, 40),
        },
        {
            "type": "worksheet",
            "name": "Subtitle",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 44, 684, 26),
        },
        {
            "type": "text",
            "runs": [
                {"text": "To view the impact of sales over time, select the "
                         "available timeframe and/or highlight values on the "
                         "trend lines.", "font_size": "8", "font_color": "#ffffff"},
                {"text": "\n", "font_size": "8", "font_color": "#ffffff"},
                {"text": "STEP 1 : SELECT A TIMEFRAME", "font_size": "8",
                 "font_color": "#ffffff", "bold": True},
            ],
            "absolute": pos(8, 72, 684, 62),
        },
        {
            "type": "worksheet",
            "name": "Timeframe Selector",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 136, 684, 32),
        },
        {
            "type": "empty",
            "style": {"background-color": "#ffffff"},
            "absolute": pos(8, 168, 684, 2),
        },
        {
            "type": "text",
            "runs": [
                {"text": "STEP 2 : HIGHLIGHT A DATE RANGE TO SEE NET CHANGE "
                         "BETWEEN DATES", "font_size": "8",
                 "font_color": "#ffffff", "bold": True},
            ],
            "absolute": pos(8, 170, 684, 24),
        },
        {
            "type": "worksheet",
            "name": "KPI",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(8, 196, 192, 250),
        },
        {
            "type": "worksheet",
            "name": "Trend",
            "show_title": False,
            "fit": "entire",
            "absolute": pos(200, 196, 492, 250),
        },
        {
            "type": "text",
            "runs": [
                {"text": "CHALLENGE BY : WILL PERKINS", "font_size": "8",
                 "font_color": "#ffffff", "font_name": "Tableau Medium",
                 "font_alignment": "0"},
            ],
            "absolute": pos(8, 452, 240, 22),
        },
        {
            "type": "text",
            "runs": [
                {"text": "#WOW2021  |  WEEK 38", "font_size": "8",
                 "font_color": "#ffffff", "font_name": "Tableau Medium",
                 "font_alignment": "1"},
            ],
            "absolute": pos(240, 452, 220, 22),
        },
        {
            "type": "text",
            "runs": [
                {"text": "RECREATED BY : DONNA COLES", "font_size": "8",
                 "font_color": "#ffffff", "font_name": "Tableau Medium",
                 "font_alignment": "2"},
            ],
            "absolute": pos(452, 452, 240, 22),
        },
        {
            "type": "text",
            "runs": [
                {"text": "https://www.workout-wednesday.com/tab2021w38/",
                 "font_size": "8", "font_color": "#ffffff",
                 "font_alignment": "1",
                 "hyperlink": 'tabdoc:load-url url="'
                              'http://www.workout-wednesday.com/tab2021w38/"'},
            ],
            "absolute": pos(8, 474, 684, 20),
        },
    ]
    editor.add_dashboard(
        DASHBOARD,
        width=700,
        height=500,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"background-color": BACKGROUND},
            "children": children,
        },
        worksheet_names=["Subtitle", "Timeframe Selector", "KPI", "Trend"],
    )

def _actions(editor, orders):
    """Wire the four interactions, each while its own source is active."""
    # The timeframe sheet writes its member into pTimeframe.
    editor.select_datasource("Date Range")
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="parameter",
        source_sheet="Timeframe Selector",
        source_field="Date Range",
        target_parameter="pTimeframe",
        aggregation="attr",
        caption="Set Timeframe",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Timeframe Selector",
        target_sheet="Timeframe Selector",
        field_mappings={"True": "False"},
        caption="Deselect Timeframe",
    )
    editor.initialize_dashboard_filter_action(
        DASHBOARD, "Deselect Timeframe", {"False": [False]}
    )

    # A drag across the trend sets the first and last day of the range.
    editor.select_datasource(orders)
    for caption, aggregation, target in (
        ("Set Start Date", "min", "pStartRange"),
        ("Set End Date", "max", "pEndRange"),
    ):
        editor.add_dashboard_action(
            DASHBOARD,
            action_type="parameter",
            source_sheet="Trend",
            source_field="[Order Date Day]",
            target_parameter=target,
            aggregation=aggregation,
            caption=caption,
        )
    # True→False: the action filter can never match, so a click deselects
    # instead of leaving the marks highlighted.
    editor.add_dashboard_action(
        DASHBOARD,
        action_type="filter",
        source_sheet="Trend",
        target_sheet="Trend",
        field_mappings={"True": "False"},
        caption="Deselect Trend",
    )
    editor.initialize_dashboard_filter_action(
        DASHBOARD, "Deselect Trend", {"False": [False]}
    )


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(ORDERS))
    # The empty template names its sample source "Sample _ Superstore (Simple)";
    # keep that caption so the primary source can be re-selected after the
    # second (Date Range) source is added.
    orders = editor.select_datasource("Sample _ Superstore (Simple)")

    _parameters(editor)
    _calculated_fields(editor)
    _trend(editor)
    _kpi(editor)
    _subtitle(editor)

    # The selector lives on its own five-row list source, as in the article.
    _timeframe_selector(editor)
    editor.select_datasource(orders)
    _dashboard(editor)
    _actions(editor, orders)

    for name in ("Trend", "KPI", "Subtitle", "Timeframe Selector"):
        editor.set_worksheet_title(name, "")
        editor.set_window_state(name, hidden=False, zoom_entire_view=True)
    editor.set_window_state(DASHBOARD, hidden=False, zoom_entire_view=True)

    output = Path(output_path) if output_path else (
        HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
