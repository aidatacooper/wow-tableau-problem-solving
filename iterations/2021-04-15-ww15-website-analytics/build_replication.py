"""Rebuild the WW15 Google Analytics website-analytics dashboard.

The challenge is a formatting/layout exercise: four metrics, each shown as a BAN
(big number) beside a weekly trend line with a reference line. Two of the
metrics are durations that must render as ``mm:ss``.

The article's chain:

- The Date range ends 2021-04-10. The author makes it a workbook-level
  (data-source scoped) filter so the aggregate LoDs never see 11/12 April; the
  locked extract already ends on 2021-04-10, so the scope is enforced by a
  context date filter on each sheet (evaluated before the LoDs).
- ``Avg Session Duration = (SUM([Session Duration]) / SUM([Sessions]))/86400``
  — seconds expressed as a fraction of a day so the ``nn:ss`` custom format
  renders minutes and seconds.
- ``Bounce Rate = SUM([Bounces])/SUM([Sessions])`` formatted ``p0.0%``.
- ``Avg Time on Page = (SUM([Time on Page])/(SUM([Pageviews]) - SUM([Exits])))/86400``
  formatted ``nn:ss``.
- ``Overall ... = {FIXED : [measure]}`` gives the aggregate value that the BAN
  shows and the trend reference line draws.
- Weeks start on Sunday, so the datasource week origin is set accordingly, and
  the axis is the continuous week-start date so 2020 and 2021 stay distinct.

Layout follows the article: one vertical container holds the title, a thin
yellow spacer "line", a second vertical container with four horizontal rows
(coloured vertical spacer + BAN + trend), and a footer row.
"""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
HYPER = HERE / "inputs/2021_04_14_WW15_Google Analytics.hyper"
DASHBOARD = "2021_04_14_WW15_WOW_Google_Analytics"
END_DATE = "2021-04-10"

PURPLE = "#7830b6"
GREEN = "#72b966"
YELLOW = "#f7cc63"
TEAL = "#58b8ba"
BLUE = "#628cb9"

# metric key -> (BAN title, sheet prefix, colour, measure, overall measure)
#
# The reference line is always Tableau's "average" formula: for sessions it
# averages the plotted weekly values, and for the other three it points at the
# pre-computed {FIXED : ...} aggregate through value-column, exactly as the
# article's reference lines do.
METRICS = [
    ("sessions", "TOTAL SESSIONS", "Sessions", PURPLE, "SUM(Sessions)", None),
    ("duration", "AVG SESSION DURATION", "Duration", TEAL, "Avg Session Duration",
     "Overall Session Duration"),
    ("bounce", "BOUNCE RATE", "Bounce Rate", GREEN, "Bounce Rate",
     "Overall Bounce Rate"),
    ("page", "AVG TIME ON PAGE", "Page Time", BLUE, "Avg Time on Page",
     "Overall Time on Page"),
]

LABEL_FORMAT = {
    "sessions": "n#,##0;-#,##0",
    "bounce": "p0.0%",
    "duration": "*nn:ss",
    "page": "*nn:ss",
}

# The extract itself ends on 2021-04-10; this context filter makes the scope
# explicit and keeps the aggregate LoDs out of any later rows.
DATE_FILTER = [
    {
        "column": "EXACTDATE(Date)",
        "type": "quantitative",
        "max": f"#{END_DATE}#",
        "context": True,
    }
]


def build():
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    # The article sets the week origin to Sunday so week numbers match.
    editor.set_date_options(start_of_week="sunday")

    # --- Measures ----------------------------------------------------------
    editor.add_calculated_field(
        "Avg Session Duration",
        "(SUM([Session Duration]) / SUM([Sessions]))/86400",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*nn:ss",
    )
    editor.add_calculated_field(
        "Bounce Rate",
        "SUM([Bounces])/SUM([Sessions])",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0.0%",
    )
    editor.add_calculated_field(
        "Avg Time on Page",
        "(SUM([Time on Page])/(SUM([Pageviews])- SUM([Exits])))/86400",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*nn:ss",
    )
    # Aggregate values for the reference lines and the BANs.
    editor.add_calculated_field(
        "Overall Session Duration",
        "{FIXED : [Avg Session Duration]}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*nn:ss",
    )
    editor.add_calculated_field(
        "Overall Bounce Rate",
        "{FIXED : [Bounce Rate]}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="p0.0%",
    )
    editor.add_calculated_field(
        "Overall Time on Page",
        "{FIXED : [Avg Time on Page]}",
        datatype="real",
        role="measure",
        field_type="quantitative",
        default_format="*nn:ss",
    )
    # The continuous weekly axis: the week-start date, so the two calendar
    # years do not collapse into 53 week-of-year buckets.
    editor.add_calculated_field(
        "Week Start",
        "DATETRUNC('week', [Date])",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    # Placeholder the author shows in the BAN tooltips.
    editor.add_calculated_field(
        "MIN(0)", "MIN(0)", datatype="integer", role="measure", field_type="quantitative"
    )

    # --- BAN and trend sheets ---------------------------------------------
    for key, title, sheet, color, measure, overall in METRICS:
        editor.add_worksheet(f"{sheet} BAN")
        editor.configure_chart(
            f"{sheet} BAN",
            mark_type="Text",
            label=measure,
            tooltip=[measure, "MIN(0)"],
            filters=DATE_FILTER,
        )
        editor.configure_custom_label(
            f"{sheet} BAN",
            [
                {"field": measure, "bold": True, "fontsize": "24"},
                {"text": "\n"},
                {"text": title, "bold": True, "fontcolor": "#000000"},
            ],
        )
        editor.configure_worksheet_style(
            f"{sheet} BAN",
            hide_axes=True,
            hide_gridlines=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            pane_cell_style={
                "text-align": "center",
                "vertical-align": "center",
                "color": color,
                "height": "73",
            },
            pane_datalabel_style={"color-mode": "match", "font-size": "8", "font-weight": "bold"},
        )

        editor.add_worksheet(f"{sheet} Profile")
        editor.configure_chart(
            f"{sheet} Profile",
            mark_type="Line",
            rows=[measure],
            columns=["EXACTDATE(Week Start)"],
            label=measure,
            detail=overall,
            tooltip=[measure, "EXACTDATE(Week Start)"],
            filters=DATE_FILTER,
        )
        editor.configure_worksheet_style(
            f"{sheet} Profile",
            hide_axes=False,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            pane_mark_style={
                "mark-labels-show": "true",
                "mark-labels-cull": "false",
                "mark-labels-mode": "most-recent",
                "mark-color": color,
            },
            pane_datalabel_style={"color-mode": "match", "font-size": "8", "font-weight": "bold"},
            axis_style={
                "per_field": [
                    {"field": "EXACTDATE(Week Start)", "attr": "title", "value": "", "scope": "cols", "class": "0"},
                    {"field": measure, "attr": "title", "value": "", "scope": "rows", "class": "0"},
                ]
            },
        )

        # Reference line: weekly average for sessions, the aggregate otherwise.
        value_field = "SUM(Sessions)" if overall is None else overall
        message = editor.add_reference_line(
            f"{sheet} Profile",
            axis_field=measure,
            value_field=value_field,
            formula="average",
            scope="per-table" if key == "sessions" else "per-pane",
            label_type="custom",
            label="AVG: <Value>" if overall is None else "OVERALL: <Value>",
            probability=None,
        )
        reference_id = message.split("'")[1]
        editor.configure_reference_line_style(
            f"{sheet} Profile",
            reference_id,
            {
                "line-visibility": "on",
                "line-pattern-only": "dotted",
                "stroke-size": "2",
                "stroke-color": "#000000",
                "color": "#000000",
                "fill-above": "#00000000",
                "fill-below": "#00000000",
                "font-size": "8",
                "text-format": LABEL_FORMAT[key],
            },
        )

    # --- Dashboard ---------------------------------------------------------
    rows = []
    for key, title, sheet, color, measure, overall in METRICS:
        rows.append(
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 219,
                "children": [
                    {
                        "type": "empty",
                        "fixed_size": 7,
                        "style": {"background-color": color},
                    },
                    {"type": "worksheet", "name": f"{sheet} BAN", "show_title": False, "fit": "entire", "fixed_size": 180},
                    {"type": "worksheet", "name": f"{sheet} Profile", "show_title": False, "fit": "entire", "weight": 1},
                ],
            }
        )

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "text",
                "runs": [
                    {"text": "#WorkoutWednesday Website Analytics", "bold": True, "font_size": "24"},
                ],
                "fixed_size": 61,
            },
            {
                "type": "empty",
                "fixed_size": 4,
                "style": {"background-color": YELLOW},
            },
            {
                "type": "container",
                "direction": "vertical",
                "children": rows,
            },
            {
                "type": "container",
                "direction": "horizontal",
                "fixed_size": 30,
                "children": [
                    {"type": "text", "runs": [{"text": "", "font_size": "8"}], "weight": 1},
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "#WORKOUTWEDNESDAY2021 WEEK 15 | BY: @ANNUJACKSON",
                                "font_size": "8",
                                "font_alignment": "2",
                            }
                        ],
                        "weight": 2,
                    },
                ],
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=1300,
        height=1000,
        layout=layout,
        worksheet_names=[f"{m[2]} {suffix}" for m in METRICS for suffix in ("BAN", "Profile")],
    )

    for key, title, sheet, color, measure, overall in METRICS:
        for suffix in ("BAN", "Profile"):
            editor.set_window_state(f"{sheet} {suffix}", hidden=False)
            editor.set_worksheet_title(f"{sheet} {suffix}", "")

    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
