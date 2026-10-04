"""Create session-height and duration-width bars using public layered mark sizing."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_11_25_WW48_Variable_Width_Bar_Chart"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    for name, formula, dtype, role, kind in [
        (
            "# of Turkeys",
            "COUNTD([User Name (Original Name)])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Duration (mins)",
            "DATEDIFF('minute',[Start time],[End time])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Duration Proportion of Day",
            "[Duration (mins)]/(24*60)",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Session Key",
            "STR([Start time])+' | '+[Session Title]+' | '+IFNULL([Location],'(null)')",
            "string",
            "dimension",
            "nominal",
        ),
    ]:
        e.add_calculated_field(
            name, formula, datatype=dtype, role=role, field_type=kind
        )
    e.add_worksheet("Viz")
    e.configure_layered_chart(
        "Viz",
        columns=["EXACTDATE(Start time)"],
        rows=["# of Turkeys", "# of Turkeys"],
        synchronized=True,
        panes=[
            {
                "mark_type": "Bar",
                "axis": "# of Turkeys",
                "color": "Location",
                "color_map": {
                    "Recording": "#664e3c",
                    "Live": "#cd806a",
                    "%null%": "#d6c8aa",
                },
                "mark_sizing_off": True,
                "mark_style": {"size": "1.0104972124099731"},
            },
            {
                "mark_type": "Bar",
                "axis": "# of Turkeys",
                "size": "AVG(Duration Proportion of Day)",
                "mark_sizing": {
                    "mark_sizing_setting": "marks-scaling-on",
                    "mark_alignment": "mark-alignment-left",
                    "use_custom_mark_size": False,
                    "custom_mark_size_in_axis_units": 1.0,
                },
                "mark_style": {"mark-color": "#ffffff", "size": "1.5"},
            },
        ],
    )
    tooltip = [
        {"field": "ATTR(Session Title)", "bold": True, "fontsize": 12},
        {"text": "\n"},
        {"field": "ATTR(Session Description)", "bold": True},
        {"text": "\n\n"},
        {"field": "# of Turkeys", "bold": True, "fontsize": 12},
        {"text": " Turkeys Attended\n"},
        {"field": "EXACTDATE(Start time)", "bold": True},
        {"text": " - "},
        {"field": "ATTR(End time)", "bold": True},
        {"text": " ["},
        {"field": "AVG(Duration (mins))", "bold": True},
        {"text": " mins]\n"},
        {"field": "ATTR(Location)"},
    ]
    for pane in range(2):
        e.configure_custom_tooltip("Viz", tooltip, pane_index=pane)
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        axis_style={
            "render-fold-reversed": "true",
            "encodings": [
                {
                    "field": "EXACTDATE(Start time)",
                    "scope": "cols",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "major-origin": "#11:30:00#",
                    "major-spacing": "15.0",
                    "major-units": "minutes",
                }
            ],
            "per_field": [
                {
                    "field": "EXACTDATE(Start time)",
                    "attr": "title",
                    "scope": "cols",
                    "class": "0",
                    "value": "",
                },
                {
                    "field": "# of Turkeys",
                    "attr": "display",
                    "scope": "rows",
                    "class": "0",
                    "value": "false",
                },
                {
                    "field": "# of Turkeys",
                    "attr": "display",
                    "scope": "rows",
                    "class": "1",
                    "value": "false",
                },
            ],
        },
        label_formats=[
            {
                "field": "EXACTDATE(Start time)",
                "text-format": "*h:nn AMPM",
                "color": "#000000",
                "font-weight": "bold",
                "font-size": "8",
            }
        ],
    )
    e.add_worksheet("Data")
    e.configure_layered_chart(
        "Data",
        rows=["Session Key"],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    "# of Turkeys",
                    "AVG(Duration (mins))",
                    "AVG(Duration Proportion of Day)",
                ],
            }
        ],
    )

    def zone(kind, x, y, width, height, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x * 100),
                "y": round(y * 100000 / 600),
                "w": round(width * 100),
                "h": round(height * 100000 / 600),
            },
            "style": {"margin": 4, "padding": 0},
            **kwargs,
        }

    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=600,
        worksheet_names=["Viz"],
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    8,
                    984,
                    80,
                    runs=[
                        {
                            "text": "Total Attendees & Session Duration",
                            "font_size": 20,
                            "font_color": "#333333",
                            "font_alignment": "0",
                            "bold": True,
                        },
                        {
                            "text": "\nTurkey Symposium 2020 | Welcome & Congratulations.. YOU MADE IT!",
                            "font_size": 10,
                            "font_color": "#333333",
                            "font_alignment": "0",
                            "bold": True,
                        },
                    ],
                ),
                zone(
                    "worksheet",
                    8,
                    88,
                    984,
                    440,
                    name="Viz",
                    show_title=False,
                    fit="entire",
                ),
                zone(
                    "text",
                    8,
                    528,
                    242,
                    32,
                    runs=[
                        {
                            "text": "DESIGNED BY : JAMI DELAGRANGE",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "0",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    250,
                    528,
                    496,
                    32,
                    runs=[
                        {
                            "text": "#WOW2020 | WEEK 48",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "1",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    746,
                    528,
                    246,
                    32,
                    runs=[
                        {
                            "text": "RECREATED WITH CWTWB",
                            "font_size": 8,
                            "font_color": "#000000",
                            "font_alignment": "2",
                            "font_name": "Tableau Medium",
                        }
                    ],
                ),
                zone(
                    "text",
                    8,
                    560,
                    984,
                    32,
                    runs=[
                        {
                            "text": "http://www.workout-wednesday.com/2020w48/",
                            "font_size": 8,
                            "font_alignment": "1",
                            "hyperlink": "http://www.workout-wednesday.com/2020w48/",
                        }
                    ],
                ),
            ],
        },
    )
    out = HERE / "outputs" / "replicated-workbook.twbx"
    out.parent.mkdir(exist_ok=True)
    e.save(str(out))
    return out


if __name__ == "__main__":
    print(build())
