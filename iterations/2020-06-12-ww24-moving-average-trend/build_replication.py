"""Rebuild county COVID moving averages, latest trend and state comparison from raw Hyper."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_06_09_WW24_MovingAvg_Covid19"
CALCS = [
    ("County", "[COUNTY_NAME]", "string", "dimension", "nominal", False),
    ("State", "[PROVINCE_STATE_NAME]", "string", "dimension", "nominal", False),
    ("Report Date", "[REPORT_DATE]", "date", "dimension", "ordinal", False),
    (
        "New Cases",
        "[PEOPLE_POSITIVE_NEW_CASES_COUNT]",
        "integer",
        "measure",
        "quantitative",
        False,
    ),
    (
        "Reported Cases",
        "[PEOPLE_POSITIVE_CASES_COUNT]",
        "integer",
        "measure",
        "quantitative",
        False,
    ),
    (
        "Valid County",
        "NOT ISNULL([COUNTY_NAME])",
        "boolean",
        "dimension",
        "nominal",
        False,
    ),
    (
        "Max Date",
        "{FIXED: MAX(IF NOT ISNULL([COUNTY_NAME]) THEN [REPORT_DATE] END)}",
        "date",
        "dimension",
        "ordinal",
        False,
    ),
    (
        "State - County",
        "[State]+' - '+[County]",
        "string",
        "dimension",
        "nominal",
        False,
    ),
    (
        "Is Selected State County?",
        "[Parameters].[State - County Parameter]=[State - County]",
        "boolean",
        "dimension",
        "nominal",
        False,
    ),
    (
        "Is Selected State?",
        "LEFT([Parameters].[State - County Parameter],FIND([Parameters].[State - County Parameter],'-')-2)=[State]",
        "boolean",
        "dimension",
        "nominal",
        False,
    ),
    (
        "3 Day Moving Avg",
        "WINDOW_AVG(SUM([New Cases]),-2,0)",
        "real",
        "measure",
        "quantitative",
        True,
    ),
    (
        "14 Day Moving Avg",
        "WINDOW_AVG(SUM([New Cases]),-13,0)",
        "real",
        "measure",
        "quantitative",
        True,
    ),
    (
        "Is Increase?",
        "IF [3 Day Moving Avg]>[14 Day Moving Avg] THEN 1 ELSE 0 END",
        "integer",
        "measure",
        "quantitative",
        True,
    ),
    (
        "Is Decrease?",
        "IF [3 Day Moving Avg]<=[14 Day Moving Avg] THEN 1 END",
        "integer",
        "measure",
        "quantitative",
        True,
    ),
    (
        "Increase | Decrease",
        "IF [Is Increase?]=1 THEN 'INCREASE' ELSE 'DECREASE' END",
        "string",
        "measure",
        "nominal",
        True,
    ),
    (
        "Match Prev Value?",
        "LOOKUP([Is Increase?],-1)=[Is Increase?]",
        "boolean",
        "measure",
        "nominal",
        True,
    ),
    (
        "Days in Trend",
        "IF FIRST()=0 OR NOT([Match Prev Value?]) THEN 1 ELSEIF [Increase | Decrease]='INCREASE' THEN [Is Increase?]+PREVIOUS_VALUE([Is Increase?]) ELSEIF [Increase | Decrease]='DECREASE' THEN [Is Decrease?]+PREVIOUS_VALUE([Is Decrease?]) END",
        "integer",
        "measure",
        "quantitative",
        True,
    ),
    (
        "Show Data for Latest Date",
        "LOOKUP(MIN([Report Date]),0)=MIN([Max Date])",
        "boolean",
        "measure",
        "nominal",
        True,
    ),
    (
        "Moving Avg To Display",
        "IF [Parameters].[Moving Avg Selector]=3 THEN [3 Day Moving Avg] ELSE [14 Day Moving Avg] END",
        "real",
        "measure",
        "quantitative",
        True,
    ),
    (
        "Map Colour",
        "IF ATTR([Is Selected State County?]) THEN [Increase | Decrease] ELSE 'OTHER' END",
        "string",
        "measure",
        "nominal",
        True,
    ),
]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/COVID-19 Activity Extract.hyper"))
    e.add_parameter(
        "Moving Avg Selector",
        datatype="integer",
        default_value="14",
        alias="14 Day Moving Avg",
        domain_type="list",
        allowed_values=["3", "14"],
        allowed_aliases={"3": "3 Day Moving Avg", "14": "14 Day Moving Avg"},
    )
    e.add_parameter(
        "State - County Parameter",
        datatype="string",
        default_value="Tennessee - Davidson",
        domain_type="any",
    )
    for name, formula, datatype, role, field_type, table_calc in CALCS:
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            table_calc="Columns" if table_calc else None,
        )
    e.set_field_geographic_role("County", "county")
    e.set_field_geographic_role("State", "state")
    e.set_geocoding_context(country="United States")
    e.set_date_options(start_of_week="monday")
    for name in [
        "New Cases",
        "Reported Cases",
        "3 Day Moving Avg",
        "14 Day Moving Avg",
        "Moving Avg To Display",
    ]:
        e.set_field_format(name, "n#,##0;-#,##0")
    e.set_field_format("Report Date", "*yyyy-mm-dd")
    e.add_calculated_field(
        "Display Date",
        "MIN([Report Date])",
        datatype="date",
        role="measure",
        field_type="ordinal",
    )
    e.set_field_format("Display Date", "*ddd, mmm d")
    e.add_calculated_field(
        "Selected Order",
        "IF [Is Selected State County?] THEN 0 ELSE 1 END",
        datatype="integer",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field(
        "Line Direction",
        "[Increase | Decrease]",
        datatype="string",
        role="measure",
        field_type="nominal",
        table_calc="Columns",
    )
    e.add_calculated_field(
        "County Sort",
        "-{FIXED [State],[County]:SUM([Reported Cases])}",
        datatype="real",
        role="dimension",
        field_type="ordinal",
    )
    e.set_datasource_color_palette(
        "Line Direction", {"DECREASE": "#76b7b2", "INCREASE": "#e15759"}
    )
    e.set_datasource_color_palette(
        "Map Colour", {"DECREASE": "#59a14f", "INCREASE": "#e15759", "OTHER": "#ffffff"}
    )
    dependencies = {
        "Line Direction": [
            "Increase | Decrease",
            "Is Increase?",
            "3 Day Moving Avg",
            "14 Day Moving Avg",
        ],
        "3 Day Moving Avg": [],
        "14 Day Moving Avg": [],
        "Is Increase?": ["3 Day Moving Avg", "14 Day Moving Avg"],
        "Is Decrease?": ["3 Day Moving Avg", "14 Day Moving Avg"],
        "Increase | Decrease": [
            "Is Increase?",
            "3 Day Moving Avg",
            "14 Day Moving Avg",
        ],
        "Match Prev Value?": ["Is Increase?", "3 Day Moving Avg", "14 Day Moving Avg"],
        "Days in Trend": [
            "Match Prev Value?",
            "Is Increase?",
            "Is Decrease?",
            "Increase | Decrease",
            "3 Day Moving Avg",
            "14 Day Moving Avg",
        ],
        "Show Data for Latest Date": [],
        "Moving Avg To Display": ["3 Day Moving Avg", "14 Day Moving Avg"],
        "Map Colour": [
            "Increase | Decrease",
            "Is Increase?",
            "3 Day Moving Avg",
            "14 Day Moving Avg",
        ],
    }

    def contexts(names, grain="[Report Date]"):
        return {
            name: [{"ordering-type": "Field", "ordering-field": grain}]
            + [
                {"field": nested, "ordering-type": "Field", "ordering-field": grain}
                for nested in dependencies[name]
            ]
            for name in names
        }

    base = [{"column": "Valid County", "values": [True]}]
    selected = base + [{"column": "Is Selected State County?", "values": [True]}]
    latest = [{"column": "Show Data for Latest Date", "values": [True]}]
    state = base + [{"column": "Is Selected State?", "values": [True]}]
    for name in ["BAN", "Map", "Bar&Line", "Table", "Data"]:
        e.add_worksheet(name)
    e.configure_layered_chart(
        "BAN",
        rows=["Is Selected State County?"],
        panes=[
            {
                "mark_type": "Text",
                "detail": "[Report Date]",
                "label": "Days in Trend",
                "labels": ["Increase | Decrease", "Display Date"],
                "label_runs": [
                    {"field": "Days in Trend", "bold": True, "fontsize": 9},
                    {"text": " day ", "fontsize": 9},
                    {"field": "Increase | Decrease", "bold": True, "fontsize": 9},
                    {"text": " as of ", "fontsize": 9},
                    {"field": "Display Date", "fontsize": 9},
                ],
            }
        ],
        filters=selected + latest,
        table_calc_overrides=contexts(
            [
                "Days in Trend",
                "Increase | Decrease",
                "Show Data for Latest Date",
            ]
        ),
    )
    e.configure_layered_chart(
        "Map",
        columns=["Longitude (generated)"],
        rows=["Latitude (generated)"],
        panes=[
            {
                "mark_type": "Multipolygon",
                "geometry": "Geometry (generated)",
                "color": "Map Colour",
                "color_map": {
                    "DECREASE": "#59a14f",
                    "INCREASE": "#e15759",
                    "OTHER": "#ffffff",
                },
                "detail": "County",
                "detail_extra": ["State", "[Report Date]", "Days in Trend"],
                "tooltip": [
                    "SUM(New Cases)",
                    "SUM(Reported Cases)",
                    "Increase | Decrease",
                ],
                "mark_style": {"mark-color": "#ffffff", "mark-stroke-color": "#787878"},
            }
        ],
        filters=state + latest,
        table_calc_overrides=contexts(
            [
                "Map Colour",
                "Days in Trend",
                "Increase | Decrease",
                "Show Data for Latest Date",
            ]
        ),
    )
    e.configure_layered_chart(
        "Bar&Line",
        columns=["EXACTDATE(Report Date)"],
        rows=["SUM(New Cases)", "Moving Avg To Display"],
        panes=[
            {
                "axis": "SUM(New Cases)",
                "mark_type": "Bar",
                "mark_sizing": {
                    "custom-mark-size-in-axis-units": 1.0,
                    "mark-alignment": "mark-alignment-left",
                    "mark-sizing-setting": "marks-scaling-on",
                    "use-custom-mark-size": False,
                },
                "tooltip": ["SUM(Reported Cases)"],
                "mark_style": {
                    "mark-color": "#ffffff",
                    "has-stroke": "true",
                    "stroke-color": "#1b1b1b",
                    "size": "2",
                },
            },
            {
                "axis": "Moving Avg To Display",
                "mark_type": "Line",
                "color": "Line Direction",
                "color_map": {"DECREASE": "#76b7b2", "INCREASE": "#e15759"},
                "tooltip": [
                    "3 Day Moving Avg",
                    "14 Day Moving Avg",
                    "Days in Trend",
                    "Increase | Decrease",
                ],
                "mark_style": {"size": "2"},
            },
        ],
        filters=selected
        + [
            {
                "column": "EXACTDATE(Report Date)",
                "type": "quantitative",
                "min": "#2020-03-08#",
            }
        ],
        table_calc_overrides=contexts(
            [
                "Moving Avg To Display",
                "Line Direction",
                "Increase | Decrease",
                "3 Day Moving Avg",
                "14 Day Moving Avg",
                "Days in Trend",
            ],
            grain="EXACTDATE(Report Date)",
        ),
    )
    for name in ["Table", "Data"]:
        e.configure_layered_chart(
            name,
            columns=["Measure Names"],
            rows=["Selected Order", "County Sort", "State", "County"],
            panes=[
                {
                    "mark_type": "Text",
                    "label": "Multiple Values",
                    "detail": "[Report Date]",
                    "detail_extra": ["Days in Trend"],
                    "tooltip": ["Increase | Decrease"],
                    "measure_values": [
                        "SUM(New Cases)",
                        "SUM(Reported Cases)",
                        "3 Day Moving Avg",
                        "14 Day Moving Avg",
                    ],
                }
            ],
            filters=state + latest if name == "Table" else state,
            table_calc_overrides=contexts(
                [
                    "3 Day Moving Avg",
                    "14 Day Moving Avg",
                    "Days in Trend",
                    "Increase | Decrease",
                ]
                + (["Show Data for Latest Date"] if name == "Table" else [])
            ),
        )
    for name in ["Table", "Data"]:
        e.set_measure_name_aliases(
            name,
            {
                "SUM(New Cases)": "New Cases",
                "SUM(Reported Cases)": "Reported\nCases",
                "3 Day Moving Avg": "3 Day Moving\nAvg",
                "14 Day Moving Avg": "14 Day\nMoving Avg",
            },
        )
        e.configure_worksheet_style(
            name,
            hide_row_label="County Sort",
            cell_formats=[
                {"font-size": 8, "text-format": "n#,##0;-#,##0"},
                {"field": "Measure Names", "width": 116},
                {"field": "County", "height": 24},
            ],
            header_formats=[{"field": "Measure Names", "height": 56}],
            label_formats=[{"field": "Measure Names", "font-size": 8}],
        )
    for name in ["BAN", "Table", "Data"]:
        e.configure_worksheet_style(
            name,
            hide_col_field_labels=True,
            hide_row_field_labels=True,
            hide_row_label="Is Selected State County?"
            if name == "BAN"
            else "Selected Order",
            hide_gridlines=True,
            hide_table_dividers=True,
            hide_sort_controls=True,
            pane_datalabel_style={"font-size": "8"},
            background_color="#f5f5f5",
        )
    e.configure_worksheet_style("BAN", pane_datalabel_style={"text-align": "left"})
    e.configure_worksheet_style(
        "Table",
        hide_row_label="State",
        label_formats=[{"field": "County", "font-size": "8"}],
        table_formats=[
            {"attr": "band-color", "value": "#eeeeee", "scope": "rows"},
            {"attr": "band-size", "value": "1", "scope": "rows"},
        ],
    )
    e.configure_worksheet_style(
        "Map",
        background_color="#f5f5f5",
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        map_style={"washout": "0.0"},
    )
    e.configure_worksheet_style(
        "Bar&Line",
        background_color="#f5f5f5",
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_gridlines=True,
        hide_zeroline=True,
        axis_style={
            "per_field": [
                {
                    "field": "Moving Avg To Display",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "SUM(New Cases)",
                    "scope": "rows",
                    "attr": "title",
                    "value": "",
                },
                {
                    "field": "EXACTDATE(Report Date)",
                    "scope": "cols",
                    "attr": "title",
                    "value": "",
                },
            ]
        },
        label_formats=[{"field": "EXACTDATE(Report Date)", "text-format": "*mmm"}],
    )

    def p(x, y, w, h):
        return {
            "x": round(x / 450 * 100000),
            "y": round(y / 1000 * 100000),
            "w": round(w / 450 * 100000),
            "h": round(h / 1000 * 100000),
        }

    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "Can you compare a 3 day vs 14 day moving average and describe the latest trend?",
                    "font_size": 12,
                    "bold": True,
                    "font_color": "#666666",
                    "font_alignment": "0",
                }
            ],
            "absolute": p(8, 8, 434, 58),
        },
        {
            "type": "paramctrl",
            "parameter": "State - County Parameter",
            "mode": "type_in",
            "show_title": False,
            "absolute": p(8, 94, 434, 37),
            "style": {"background-color": "#f5f5f5"},
        },
        {
            "type": "worksheet",
            "name": "BAN",
            "fit": "entire",
            "show_title": False,
            "absolute": p(8, 131, 434, 39),
        },
        {
            "type": "worksheet",
            "name": "Map",
            "fit": "entire",
            "show_title": False,
            "absolute": p(8, 170, 434, 243),
        },
        {
            "type": "paramctrl",
            "parameter": "Moving Avg Selector",
            "mode": "compact",
            "show_title": False,
            "absolute": p(8, 413, 190, 44),
        },
        {
            "type": "color",
            "worksheet": "Bar&Line",
            "field": "Line Direction",
            "pane_index": 2,
            "show_title": False,
            "absolute": p(202, 413, 240, 44),
            "style": {"flow-direction": "horizontal"},
        },
        {
            "type": "worksheet",
            "name": "Bar&Line",
            "fit": "entire",
            "show_title": False,
            "absolute": p(8, 457, 434, 135),
        },
        {
            "type": "worksheet",
            "name": "Table",
            "fit": "width",
            "show_title": False,
            "absolute": p(8, 592, 434, 345),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "DESIGNED BY: JAMI DELAGRANGE\nRECREATED WITH CWTWB",
                    "font_size": 8,
                }
            ],
            "absolute": p(8, 937, 236, 55),
        },
        {
            "type": "text",
            "runs": [
                {"text": "#WOW2020 | WEEK 24\nDATA: Tableau COVID-19", "font_size": 8}
            ],
            "absolute": p(244, 937, 198, 55),
        },
    ]
    zones.insert(
        0,
        {
            "type": "empty",
            "absolute": p(8, 70, 434, 867),
            "style": {"background-color": "#f5f5f5"},
        },
    )
    zones.append(
        {
            "type": "text",
            "runs": [
                {
                    "text": 'Search "State - County"',
                    "font_size": 9,
                    "font_alignment": "0",
                }
            ],
            "absolute": p(8, 70, 434, 24),
            "style": {"background-color": "#f5f5f5"},
        }
    )
    e.add_dashboard(
        DASHBOARD,
        width=450,
        height=1000,
        worksheet_names=["BAN", "Map", "Bar&Line", "Table"],
        layout={"type": "container", "direction": "floating", "children": zones},
    )
    e.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(exist_ok=True)
    e.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
