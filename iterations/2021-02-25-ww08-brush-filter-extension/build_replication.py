"""Build borough time series and the real sandboxed Brush Filter extension."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_02_24_WW08_Brush_Filter_Extension"
EXTENSION_ID = "com.starschema.extension.brushfilter.sandboxed"
EXTENSION_URL = (
    "https://extensions.tableauusercontent.com/sandbox/brush-filter/index.html"
)
BOROUGHS = ["BROOKLYN", "MANHATTAN", "BRONX", "QUEENS", "STATEN ISLAND"]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(
        str(HERE / "inputs/2021_02_24_WW08_Rat_Sightings.hyper")
    )
    editor.add_calculated_field(
        "# of Sightings", "COUNT([Created Date])", datatype="integer"
    )
    editor.add_calculated_field(
        "Borough Sort",
        "CASE [Borough] WHEN 'BROOKLYN' THEN 5 WHEN 'MANHATTAN' THEN 4 WHEN 'BRONX' THEN 3 WHEN 'QUEENS' THEN 2 WHEN 'STATEN ISLAND' THEN 1 END",
        datatype="integer",
    )
    formulas = {
        "Start Count": (
            "WINDOW_MAX(IF FIRST()=0 THEN [# of Sightings] END)",
            "integer",
        ),
        "End Count": ("WINDOW_MAX(IF LAST()=0 THEN [# of Sightings] END)", "integer"),
        "Change": (
            "IF [End Count]-[Start Count]>0 THEN 'INCREASE' ELSEIF [End Count]-[Start Count]<0 THEN 'DECREASE' ELSE 'NO CHANGE' END",
            "string",
        ),
        "Start Month": (
            "WINDOW_MAX(IF FIRST()=0 THEN MIN([Created Date]) END)",
            "date",
        ),
        "End Month": ("WINDOW_MAX(IF LAST()=0 THEN MIN([Created Date]) END)", "date"),
    }
    for name, (formula, datatype) in formulas.items():
        editor.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role="measure",
            field_type="nominal" if datatype == "string" else "quantitative",
            table_calc="Rows",
        )
    editor.set_field_format("Created Date", "*mmm yy")
    for field in ["Start Month", "End Month"]:
        editor.set_field_format(field, "*mmmm yyyy")
    editor.add_worksheet("by Borough")
    addressed = {
        "ordering_type": "Field",
        "order": [{"field": "MONTHTRUNC(Created Date)", "reference": "instance"}],
    }
    editor.configure_layered_chart(
        "by Borough",
        columns=["Borough", "MONTHTRUNC(Created Date)"],
        rows=["# of Sightings"],
        panes=[
            {
                "axis": "# of Sightings",
                "mark_type": "Line",
                "color": "Change",
                "color_map": {
                    "INCREASE": "#f28e2b",
                    "DECREASE": "#31a1b3",
                    "NO CHANGE": "#b4b7b7",
                },
                "detail_extra": [
                    "Start Month",
                    "End Month",
                    "Start Count",
                    "End Count",
                    "MIN(Borough Sort)",
                ],
                "tooltip": ["Borough", "MONTHTRUNC(Created Date)", "# of Sightings"],
                "selection_relaxation": "selection-relaxation-disallow",
            }
        ],
        table_calc_overrides={
            "Change": [
                {"ordering_type": "Rows"},
                {"field": "End Count", **addressed},
                {"field": "Start Count", **addressed},
            ],
            "Start Count": [addressed],
            "End Count": [addressed],
            "Start Month": [{"ordering_type": "Rows"}],
            "End Month": [{"ordering_type": "Rows"}],
        },
        sort_descending="MIN(Borough Sort)",
        sort_field="Borough",
        sort_mode="computed",
        filters=[
            {"column": "Borough", "values": ["Unspecified"], "exclude": True},
            {
                "column": "MONTHTRUNC(Created Date)",
                "type": "quantitative",
                "min": "#2010-01-01 00:00:00#",
                "max": "#2021-02-01 00:00:00#",
            },
        ],
    )
    editor.configure_custom_tooltip(
        "by Borough",
        [
            {"field": "# of Sightings", "bold": True},
            {"text": " rat sightings in "},
            {"field": "Borough", "bold": True},
            {"text": " during "},
            {"field": "MONTHTRUNC(Created Date)", "bold": True},
        ],
    )
    editor.configure_worksheet_style(
        "by Borough",
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        axis_style={
            "per_field": [
                {
                    "field": "# of Sightings",
                    "scope": "rows",
                    "attr": "title",
                    "class": "0",
                    "value": "",
                },
                {
                    "field": "MONTHTRUNC(Created Date)",
                    "scope": "cols",
                    "attr": "title",
                    "class": "0",
                    "value": "",
                },
            ]
        },
        label_formats=[{"field": "Borough", "font-size": "8", "font-weight": "bold"}],
    )
    editor.set_worksheet_rich_title(
        "by Borough",
        [
            {
                "text": "Between <Start Month> & <End Month>\n",
                "fontsize": 12,
                "bold": True,
            },
            {"text": "INCREASE", "fontsize": 12, "bold": True, "fontcolor": "#f3963b"},
            {"text": "  |  ", "fontsize": 12, "bold": True},
            {"text": "DECREASE", "fontsize": 12, "bold": True, "fontcolor": "#3ba1b1"},
            {"text": "  |  ", "fontsize": 12, "bold": True},
            {"text": "NO CHANGE", "fontsize": 12, "bold": True, "fontcolor": "#b2b6b6"},
        ],
    )
    editor.add_dashboard(
        DASHBOARD,
        width=1366,
        height=768,
        layout={
            "type": "container",
            "style": {"margin": 8},
            "children": [
                {
                    "type": "text",
                    "fixed_size": 55,
                    "runs": [
                        {
                            "text": "How many RATS have been seen in NYC over time?",
                            "bold": True,
                            "font_size": 15,
                            "font_color": "#027b8e",
                            "font_alignment": 1,
                        }
                    ],
                },
                {
                    "type": "text",
                    "fixed_size": 29,
                    "runs": [
                        {
                            "text": "Use your mouse to brush along the timeline below to filter | drag the grey box to change the time period | drag either end of the grey box to expand or shorten the time period",
                            "bold": True,
                            "font_size": 8,
                        }
                    ],
                },
                {"type": "empty", "fixed_size": 141},
                {
                    "type": "worksheet",
                    "name": "by Borough",
                    "show_title": True,
                    "fit": "entire",
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 32,
                    "children": [
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "CHALLENGE BY : SEAN MILLER",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "#WOW2021  |  WEEK 8  |  DATA: NYC 311",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                    "font_alignment": 1,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "RECREATED WITH CWTWB",
                                    "font_size": 8,
                                    "font_color": "#027b8e",
                                    "font_alignment": 2,
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "fixed_size": 32,
                    "runs": [
                        {
                            "text": "http://www.workout-wednesday.com/2021w08tab/",
                            "font_size": 8,
                            "font_alignment": 1,
                        }
                    ],
                },
            ],
        },
    )
    editor.add_dashboard_extension(
        DASHBOARD,
        {
            "id": EXTENSION_ID,
            "version": "0.1.0",
            "url": EXTENSION_URL,
            "name": "",
            "name_resource_id": "name",
            "resources": {"name": {"en_US": "Brush Filter"}},
            "description": "Provides interactive data filtering with brushing. (region specification with mouse gestures).",
            "author": {
                "name": "Starschema",
                "email": "extensions@starschema.com",
                "organization": "Starschema",
                "website": "https://starschema.com",
            },
            "min_api_version": "1.1",
            "configure_menu": True,
        },
        {
            "chartBackgroundColor": "#ffffff",
            "chartColor": "#0093a7",
            "sheetIdSetting": "0",
            "vizBackgroundColor": "#ffffff",
            "xAxisSetting": "MONTH(Created Date)",
            "yAxisSetting": "AGG(# of Sightings)",
        },
        x=586,
        y=12049,
        width=98828,
        height=18420,
    )
    editor.set_window_state("by Borough", hidden=False, zoom_entire_view=True)
    editor.set_window_state(DASHBOARD, maximized=True, zoom_entire_view=True)
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    editor.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
