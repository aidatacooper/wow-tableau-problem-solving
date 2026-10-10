"""Build WW14 (2023) from extracted Hyper data with public cwtwb APIs only.

The author workbook is analysis evidence and is never read here. Every number
this builder produces is recomputed from inputs/ (see verify_replication.py for
the independent Hyper aggregate).
"""

from pathlib import Path

from cwtwb import TWBEditor

ITERATION_DIR = Path(__file__).resolve().parent
HYPER = ITERATION_DIR / "inputs" / "2023_04_05_WW14_Baseball.hyper"
OUTPUT_DIR = ITERATION_DIR / "outputs"

DASHBOARD = "2023_04_05_WW14_Baseball_Games"

MIN_YEAR = 1960


def build(output_path: Path) -> Path:
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HYPER))

    for name, formula, extra, datatype, role, field_type, fmt in [
        (
            "Duration (mins)",
            "DATEPART('hour', [Time/9I]) * 60 + DATEPART('minute', [Time/9I])",
            {},
            "integer",
            "measure",
            "quantitative",
            "",
        ),
        (
            "Decade",
            "STR(FLOOR([Year] / 10) * 10) + 's'",
            {},
            "string",
            "dimension",
            "nominal",
            "",
        ),
        (
            # The author plots INDEX() as a discrete pill on Columns, computing
            # by Year only, and hides its header. It spaces years left-to-right.
            "Index",
            "INDEX()",
            {"table_calc": {"ordering-field": "[Year]", "ordering-type": "Field"}},
            "integer",
            "measure",
            "quantitative",
            "",
        ),
        (
            "Latest Duration",
            "WINDOW_MAX(IF LAST() = 0 THEN SUM([Duration (mins)]) END)",
            {"table_calc": {"ordering-field": "[Year]", "ordering-type": "Field"}},
            "integer",
            "measure",
            "quantitative",
            "",
        ),
        (
            "Duration > Latest",
            "SUM([Duration (mins)]) >= [Latest Duration]",
            {"table_calc": "Rows"},
            "boolean",
            "measure",
            "nominal",
            "",
        ),
        (
            # Year is an integer dimension in the extract; an explicit ordinal
            # calculated field gives the discrete [none:...:ok] instance the
            # author binds on Detail/Label.
            "Year Label",
            "STR([Year])",
            {},
            "string",
            "dimension",
            "ordinal",
            "",
        ),
    ]:
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            default_format=fmt,
            **extra,
        )

    editor.set_field_format("Time/9I", "*h:nn")

    # ---- Viz: bar per Year inside Decade rows, coloured by Duration > Latest
    editor.add_worksheet("Viz")
    editor.configure_chart(
        "Viz",
        mark_type="Bar",
        columns=["Index"],
        rows=["Decade", "SUM(Duration (mins))"],
        color="Duration > Latest",
        detail="Latest Duration",
        # The author stacks the year above the h:nn duration in one
        # bottom-centred label.
        label="Year Label",
        label_extra=["ATTR(Time/9I)"],
        label_runs=[
            {"field": "Year Label", "bold": True},
            {"text": "\n", "fontcolor": "#000000"},
            {"field": "ATTR(Time/9I)"},
        ],
        sort_field="Index",
        table_calc_overrides={
            # Both table calcs address the Year dimension.
            "Index": [{"ordering-field": "Year Label", "ordering-type": "Field"}],
            "Latest Duration": [{"ordering-field": "Year Label", "ordering-type": "Field"}],
            "Duration > Latest": [
                {"ordering-type": "Rows"},
                {
                    "field": "Latest Duration",
                    "ordering-type": "Field",
                    "order": ["Decade", "Year Label"],
                },
            ],
        },
        filters=[{"column": "[Year]", "type": "quantitative", "min": str(MIN_YEAR)}],
    )
    editor.configure_custom_tooltip(
        "Viz",
        runs=[
            {"text": "Decade:\t"},
            {"field": "Decade", "bold": True},
            {"text": "\nYear:\t"},
            {"field": "Year", "bold": True},
            {"text": "\nDuration (mins): "},
            {"field": "SUM(Duration (mins))", "bold": True},
            {"text": "\nLatest Duration: "},
            {"field": "Latest Duration", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "Viz",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=True,
        label_formats=[
            # The Index pill spaces years left-to-right; its header is hidden.
            {"field": "Index", "attr": "display", "value": "false"},
        ],
        # The colour legend is redundant — every bar is labelled by year and
        # the author hides both the colour legend and the measure header.
        legend_style={"display": "false"},
        pane_cell_style={"vertical-align": "bottom"},
        pane_datalabel_style={"color-mode": "user", "color": "#000000"},
        pane_mark_style={"mark-labels-show": "true", "mark-labels-cull": "false"},
    )
    editor.add_reference_line(
        "Viz",
        axis_field="SUM(Duration (mins))",
        value_field="Latest Duration",
        formula="average",
        scope="per-pane",
        label_type="custom",
        label="2:38 in 2023",
        probability=None,
        tooltip="",
    )
    editor.configure_reference_line_style(
        "Viz",
        "refline0",
        {
            "line-visibility": "on",
            "line-pattern-only": "solid",
            "stroke-size": "2",
            "text-align": "right",
            "fill-above": "#00000000",
            "fill-below": "#00000000",
        },
    )

    # ---- Data: the author's hidden text-table companion sheet
    editor.add_worksheet("Data")
    editor.configure_chart(
        "Data",
        mark_type="Text",
        rows=["Year", "Decade", "Index", "Duration > Latest"],
        measure_values=["SUM(Duration (mins))", "Latest Duration"],
        label="Multiple Values",
        sort_field="Index",
        table_calc_overrides={
            "Index": [{"ordering-field": "Year Label", "ordering-type": "Field"}],
            "Duration > Latest": [
                {"ordering-type": "Rows"},
                {
                    "field": "Latest Duration",
                    "ordering-type": "Field",
                    "order": ["Decade", "Year Label"],
                },
            ],
        },
        filters=[{"column": "[Year]", "type": "quantitative", "min": str(MIN_YEAR)}],
    )

    layout = {
        "type": "container",
        "direction": "floating",
        "style": {"background-color": "#ffffff"},
        "children": [
            {
                "type": "worksheet",
                "name": "Viz",
                "show_title": False,
                "fit": "entire",
                "absolute": {"x": 1143, "y": 1143, "w": 97714, "h": 88571},
            },
            {
                "type": "text",
                "text": "CHALLENGE BY : SPENCER BAUCKE",
                "runs": [
                    {
                        "text": "CHALLENGE BY : SPENCER BAUCKE",
                        "font_size": "8",
                        "font_color": "#000000",
                        "font_alignment": "0",
                    }
                ],
                "absolute": {"x": 1143, "y": 89714, "w": 36190, "h": 4572},
            },
            {
                "type": "text",
                "text": "#WOW2023  |  WEEK 14 ",
                "runs": [
                    {
                        "text": "#WOW2023  |  WEEK 14 ",
                        "font_size": "8",
                        "font_color": "#000000",
                        "font_alignment": "1",
                    }
                ],
                "absolute": {"x": 37333, "y": 89714, "w": 31048, "h": 4572},
            },
            {
                "type": "text",
                "text": "RECREATED BY : DONNA COLES",
                "runs": [
                    {
                        "text": "RECREATED BY : DONNA COLES",
                        "font_size": "8",
                        "font_color": "#000000",
                        "font_alignment": "2",
                    }
                ],
                "absolute": {"x": 68381, "y": 89714, "w": 30476, "h": 4572},
            },
            {
                "type": "text",
                "text": " DATA https://www.baseball-reference.com/",
                "runs": [
                    {
                        "text": " DATA ",
                        "font_size": "8",
                        "font_color": "#000000",
                        "font_alignment": "1",
                    },
                    {
                        "text": "https://www.baseball-reference.com/",
                        "font_size": "8",
                        "font_color": "#000000",
                        "font_alignment": "1",
                    },
                ],
                "absolute": {"x": 1143, "y": 94286, "w": 97714, "h": 4571},
            },
        ],
    }
    editor.add_dashboard(
        DASHBOARD,
        width=700,
        height=700,
        layout=layout,
        worksheet_names=["Viz", "Data"],
    )
    editor.set_worksheet_hidden("Data")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_path, validate=False)
    return output_path


if __name__ == "__main__":
    for filename in (
        "2023-04-07-ww14-baseball-game-duration-replicated-workbook.twb",
        "replicated-workbook.twbx",
    ):
        print(build(OUTPUT_DIR / filename))
