"""Rebuild standings, stacked points and the last five results from three extracts."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_11_11_WW46_Premier_League_Table"
FACTS = "TEMP_1f3qskj0te9n9v1f3avp71ojhhal.hyper"
HOME = "TEMP_0jwezo318cddv716gtx140t8vf36.hyper"
AWAY = "TEMP_1utfxg4148kl101dumirh0r0cn6d.hyper"


def zone(kind, x, y, w, h, **kwargs):
    return {
        "type": kind,
        "absolute": {
            "x": round(x * 125),
            "y": round(y * 100000 / 735),
            "w": round(w * 125),
            "h": round(h * 100000 / 735),
        },
        "style": {"margin": 0, "padding": 0},
        **kwargs,
    }


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / FACTS))
    primary = e.select_datasource("Sample _ Superstore (Simple)")
    home = e.add_hyper_datasource("EPL - Home", str(HERE / "inputs" / HOME))
    e.add_calculated_field(
        "BLEND Team",
        "[HomeTeam]",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    away = e.add_hyper_datasource("EPL - Away", str(HERE / "inputs" / AWAY))
    e.add_calculated_field(
        "BLEND Team",
        "[AwayTeam]",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.select_datasource(primary)
    specs = [
        ("Team", "[Pivot Field Values]", "string", "dimension", "nominal", None),
        ("Home or Away", "[Pivot Field Names]", "string", "dimension", "nominal", None),
        ("BLEND Team", "[Team]", "string", "dimension", "nominal", None),
        (
            "Win-Loss-Draw",
            "IF [Home or Away]='Home Team' AND [FTR]='H' THEN 'W' ELSEIF [Home or Away]='Away Team' AND [FTR]='A' THEN 'W' ELSEIF [FTR]='D' THEN 'T' ELSE 'L' END",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        (
            "Points",
            "IF [Win-Loss-Draw]='W' THEN 3 ELSEIF [Win-Loss-Draw]='T' THEN 1 ELSE 0 END",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Matches Played",
            "{FIXED [Team]: COUNT([Date])}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Wins",
            "{FIXED [Team]: SUM(IF [Win-Loss-Draw]='W' THEN 1 ELSE 0 END)}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Ties",
            "{FIXED [Team]: SUM(IF [Win-Loss-Draw]='T' THEN 1 ELSE 0 END)}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Losses",
            "{FIXED [Team]: SUM(IF [Win-Loss-Draw]='L' THEN 1 ELSE 0 END)}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Total Points",
            "{FIXED [Team]: SUM([Points])}",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Colour WLD Circle",
            "[Win-Loss-Draw]",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        (
            "Team Score",
            "IF [Home or Away]='Home Team' THEN [FTHG] ELSE [FTAG] END",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Opposition Score",
            "IF [Home or Away]='Away Team' THEN [FTHG] ELSE [FTAG] END",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        ("Index", "INDEX()", "integer", "measure", "quantitative", "Columns"),
        ("Size", "SIZE()", "integer", "measure", "quantitative", "Rows"),
        (
            "Last 5 matches only",
            "[Index]>[Size]-5",
            "boolean",
            "measure",
            "nominal",
            "Rows",
        ),
        (
            "Index To Plot",
            "[Index]-([Size]-5)",
            "integer",
            "measure",
            "quantitative",
            "Columns",
        ),
    ]
    for name, formula, datatype, role, kind, tc in specs:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind, table_calc=tc
        )
    e.import_blended_field("Home Opposition", home, "ATTR(AwayTeam)")
    e.import_blended_field("Away Opposition", away, "ATTR(HomeTeam)")
    e.add_calculated_field(
        "Opposition",
        "IF ISNULL([Home Opposition]) THEN [Away Opposition] ELSE [Home Opposition] END",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    for field in (
        "Points",
        "Matches Played",
        "Wins",
        "Ties",
        "Losses",
        "Total Points",
        "Team Score",
        "Opposition Score",
    ):
        e.set_field_format(field, "n#,##0;-#,##0")
    e.set_datasource_color_palette(
        "Win-Loss-Draw", {"W": "#137547", "T": "#dddddd", "L": "#fed7db"}
    )
    e.set_datasource_color_palette(
        "Colour WLD Circle", {"W": "#59a14f", "T": "#bab0ac", "L": "#e15759"}
    )
    for name in ("Table", "Bar", "Chart"):
        e.add_worksheet(name)
    e.configure_layered_chart(
        "Table",
        columns=["Measure Names"],
        rows=["Team"],
        axis_shelf="columns",
        panes=[
            {
                "mark_type": "Automatic",
                "label": "Multiple Values",
                "measure_values": [
                    "SUM(Matches Played)",
                    "SUM(Wins)",
                    "SUM(Ties)",
                    "SUM(Losses)",
                ],
            }
        ],
        sort_descending="SUM(Points)",
        sort_field="Team",
        sort_mode="computed",
    )
    e.configure_worksheet_style(
        "Table",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_sort_controls=True,
        hide_row_field_labels=False,
        hide_band_color=True,
        table_formats=[
            {"attr": "band-color", "value": "#ffffff"},
            {"attr": "band-color", "scope": "rows", "value": "#ffffff"},
        ],
        pane_datalabel_style={"font-size": "9"},
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
        header_formats=[
            {"field": "Measure Names", "height": 56},
            {"field": "Team", "width": 124},
        ],
        cell_formats=[{"field": "Measure Names", "width": 74}],
        label_formats=[
            {"field": "Measure Names", "font-size": 9},
            {
                "field": "Team",
                "font-size": 9,
                "font-family": "Tableau Book",
                "text-align": "left",
            },
        ],
        table_dividers=[
            {
                "scope": "rows",
                "div-level": 1,
                "stroke-color": "#e6e6e6",
                "stroke-size": 1,
                "line-visibility": "on",
            }
        ],
    )
    e.configure_layered_chart(
        "Bar",
        columns=["SUM(Points)", "SUM(Total Points)"],
        rows=["Team"],
        axis_shelf="columns",
        hide_axes=True,
        sort_descending="SUM(Points)",
        sort_field="Team",
        sort_mode="computed",
        panes=[
            {
                "axis": "SUM(Points)",
                "mark_type": "Bar",
                "color": "Win-Loss-Draw",
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "0.6366850733757019",
                    "mark-labels-show": "false",
                },
            },
            {
                "axis": "SUM(Total Points)",
                "mark_type": "GanttBar",
                "label": "SUM(Total Points)",
                "mark_sizing_off": True,
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                    "mark-color": "#00000000",
                    "size": "0.0099999997764825821",
                    "mark-transparency": "0",
                },
            },
        ],
    )
    e.configure_worksheet_style(
        "Bar",
        hide_row_label="Team",
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        pane_datalabel_style={"font-size": "9"},
        table_dividers=[
            {
                "scope": "rows",
                "div-level": 1,
                "stroke-color": "#e6e6e6",
                "stroke-size": 1,
                "line-visibility": "on",
            }
        ],
    )
    order = {
        "ordering_type": "Field",
        "order": ["Date", "Colour WLD Circle", "Win-Loss-Draw"],
    }
    nested = [
        {"ordering_type": "Columns"},
        {"field": "Index", **order},
        {"field": "Size", **order},
    ]
    e.configure_layered_chart(
        "Chart",
        columns=["Index To Plot"],
        rows=["Team"],
        axis_shelf="columns",
        hide_axes=True,
        sort_descending="SUM(Points)",
        sort_field="Team",
        sort_mode="computed",
        table_calc_context=True,
        table_calc_overrides={
            "Index To Plot": [{"ordering_type": "Rows"}, *nested[1:]],
            "Last 5 matches only": nested,
        },
        filters=[
            {"column": "Last 5 matches only", "values": [True], "type": "categorical"}
        ],
        panes=[
            {
                "axis": "Index To Plot",
                "mark_type": "Circle",
                "color": "Colour WLD Circle",
                "label": "Colour WLD Circle",
                "detail": "EXACTDATE(Date)",
                "detail_extra": ["Win-Loss-Draw"],
                "tooltip": ["SUM(Team Score)", "SUM(Opposition Score)", "Opposition"],
                "mark_sizing_off": True,
                "mark_style": {
                    "size": "1.2413811683654785",
                    "mark-transparency": "57",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
            }
        ],
    )
    for secondary, field in ((home, "ATTR(AwayTeam)"), (away, "ATTR(HomeTeam)")):
        e.configure_datasource_blend(
            "Chart", secondary, {"BLEND Team": "BLEND Team", "Date": "Date"}, [field]
        )
    e.configure_worksheet_style(
        "Chart",
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={
            "color-mode": "match",
            "font-size": "8",
            "font-weight": "bold",
        },
        hide_row_label="Team",
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        axis_style={
            "per_field": [
                {
                    "field": "Index To Plot",
                    "attr": "display",
                    "scope": "cols",
                    "value": "false",
                }
            ]
        },
        table_dividers=[
            {
                "scope": "rows",
                "div-level": 1,
                "stroke-color": "#e6e6e6",
                "stroke-size": 1,
                "line-visibility": "on",
            }
        ],
    )
    e.configure_custom_tooltip(
        "Chart",
        [
            {"field": "EXACTDATE(Date)", "bold": True},
            {"text": " vs. "},
            {"field": "Opposition", "bold": True},
            {"text": "\n"},
            {"field": "SUM(Team Score)"},
            {"text": "-"},
            {"field": "SUM(Opposition Score)"},
            {"text": " ("},
            {"field": "Win-Loss-Draw"},
            {"text": ")"},
        ],
    )
    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=735,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    8,
                    784,
                    32,
                    runs=[
                        {
                            "text": "CAN YOU BUILD A PREMIER LEAGUE TABLE?",
                            "font_size": 18,
                        }
                    ],
                ),
                zone(
                    "worksheet",
                    8,
                    40,
                    403,
                    622,
                    name="Table",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "text",
                    411,
                    40,
                    185,
                    55,
                    runs=[{"text": "Total Points", "font_size": 9}],
                ),
                zone(
                    "text",
                    596,
                    40,
                    196,
                    55,
                    runs=[{"text": "Last 5 Matches", "font_size": 9}],
                ),
                zone(
                    "worksheet",
                    411,
                    95,
                    185,
                    567,
                    name="Bar",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "worksheet",
                    596,
                    95,
                    196,
                    567,
                    name="Chart",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "text",
                    8,
                    663,
                    262,
                    32,
                    runs=[{"text": "DESIGNED BY : LUKE STANKE", "font_size": 9}],
                ),
                zone(
                    "text",
                    270,
                    663,
                    261,
                    32,
                    runs=[{"text": "#WOW2020  |  WEEK 46", "font_size": 9}],
                ),
                zone(
                    "text",
                    531,
                    663,
                    261,
                    32,
                    runs=[{"text": "RECREATED BY : DONNA COLES", "font_size": 9}],
                ),
                zone(
                    "text",
                    8,
                    695,
                    784,
                    32,
                    runs=[
                        {
                            "text": "http://www.workout-wednesday.com/2020w46/",
                            "font_size": 9,
                        }
                    ],
                ),
            ],
        },
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
