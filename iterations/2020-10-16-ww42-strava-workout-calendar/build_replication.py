"""Build a three-sheet training calendar from two separate blended extracts."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_10_14_WW42_Strava_Dashboard"
CALENDAR = "TEMP_1bdxkpy13x6eq915qhj8e16rn32h.hyper"
ACTIVITIES = "TEMP_04r3f5b0jg8h101drwlwq0pqgfqk.hyper"


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / CALENDAR))
    primary = e.select_datasource("Sample _ Superstore (Simple)")
    secondary = e.add_hyper_datasource(
        "Activities Summary", str(HERE / "inputs" / ACTIVITIES)
    )
    e.set_date_options(start_of_week="monday")
    e.add_calculated_field(
        "BLEND: Date",
        "DATE([DateTime])",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.add_calculated_field("Activity Hours", "[Seconds]/3600.0")
    e.add_calculated_field("Activity Count", "COUNT([Activity ID])", datatype="integer")
    e.select_datasource(primary)
    e.set_date_options(start_of_week="monday")
    e.add_calculated_field(
        "BLEND: Date", "[Date]", datatype="date", role="dimension", field_type="ordinal"
    )
    for alias, field in [
        ("Blended Hours", "SUM(Activity Hours)"),
        ("Blended Miles", "SUM(Miles)"),
        ("Blended Activities", "Activity Count"),
    ]:
        e.import_blended_field(alias, secondary, field)
    for alias, source in [
        ("Hours", "Blended Hours"),
        ("Miles", "Blended Miles"),
        ("# Actvities", "Blended Activities"),
    ]:
        e.add_calculated_field(
            alias,
            f"ZN([{source}])",
            datatype="integer" if alias == "# Actvities" else "real",
        )
        e.set_field_format(
            alias, "n#,##0;-#,##0" if alias == "# Actvities" else "n#,##0.0;-#,##0.0"
        )
    dimensions = [
        (
            "Rows",
            "IF MONTH([Date])<=4 THEN 0 ELSEIF MONTH([Date])<=8 THEN 1 ELSE 2 END",
            "integer",
            "ordinal",
        ),
        ("Cols", "(MONTH([Date])-1)%4", "integer", "ordinal"),
        ("Month", "DATE(DATETRUNC('month',[Date]))", "date", "ordinal"),
        (
            "Month Name Abbrev",
            "IF DAY([Date])=28 THEN UPPER(LEFT(DATENAME('month',[Date]),3)) END",
            "string",
            "nominal",
        ),
        ("LABEL:Hours", "IF DAY([Date])=28 THEN 'HOURS' END", "string", "nominal"),
        ("True", "TRUE", "boolean", "nominal"),
        ("False", "FALSE", "boolean", "nominal"),
    ]
    for name, formula, dtype, ftype in dimensions:
        e.add_calculated_field(
            name, formula, datatype=dtype, role="dimension", field_type=ftype
        )
    e.add_calculated_field(
        "Hours in Month",
        "IF MIN(DAY([Date]))=28 THEN WINDOW_SUM([Hours]) END",
        table_calc="Rows",
    )
    e.set_field_format("Hours in Month", "n#,##0;-#,##0")
    e.add_calculated_field(
        "Label : Year",
        "YEAR(WINDOW_MAX(MAX([BLEND: Date])))",
        datatype="integer",
        table_calc="Rows",
    )
    e.set_field_format("Label : Year", "n0;-0")
    for axis in ["Monthly Summary Axis", "Hours Axis", "Miles Axis", "Activities Axis"]:
        e.add_calculated_field(axis, "MIN(0)")
    filters = [{"column": "YEAR(BLEND: Date)", "values": [2020]}]
    for sheet in ["Calendar", "Weekly Profile", "BANs"]:
        e.add_worksheet(sheet)

    e.configure_dual_axis(
        "Calendar",
        columns=["Cols", "DAY(Date)"],
        rows=["Rows", "Monthly Summary Axis", "Hours"],
        mark_type_1="Text",
        mark_type_2="Bar",
        label_1="Hours in Month",
        detail_1="EXACTDATE(Date)",
        detail_2="EXACTDATE(Date)",
        synchronized=False,
        fold_axis=False,
        show_labels=False,
        mark_color_2="#000000",
        size_value_2="0.6366850733757019",
        filters=filters,
        table_calc_overrides={
            "Hours in Month": [
                {
                    "ordering_type": "Field",
                    "order": [
                        {"field": "DAY(Date)", "reference": "instance"},
                        {"field": "EXACTDATE(Date)", "reference": "instance"},
                        "Month Name Abbrev",
                        "LABEL:Hours",
                    ],
                }
            ]
        },
    )
    for pane_index in [0, 1, 2]:
        e.configure_custom_tooltip(
            "Calendar", [{"field": "True"}, {"field": "False"}], pane_index=pane_index
        )
    e.configure_custom_label(
        "Calendar",
        [
            {
                "field": "Month Name Abbrev",
                "fontsize": 16,
                "fontname": "Times New Roman",
                "fontcolor": "#898989",
            },
            {"text": "\n"},
            {"field": "Hours in Month", "fontsize": 16, "fontname": "Times New Roman"},
            {"text": "\n"},
            {
                "field": "LABEL:Hours",
                "fontsize": 9,
                "fontname": "Times New Roman",
                "fontcolor": "#898989",
            },
        ],
        pane_index=1,
    )
    e.configure_worksheet_style(
        "Calendar",
        panes_style={
            1: {
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
                "cell_style": {"text-align": "right"},
            },
            2: {"mark_style": {"mark-labels-show": "false", "has-stroke": "false"}},
        },
    )
    e.configure_layered_chart(
        "Weekly Profile",
        columns=["WEEK(BLEND: Date)"],
        rows=["Hours"],
        panes=[
            {
                "axis": "Hours",
                "mark_type": "Bar",
                "detail_extra": ["True", "False"],
                "tooltip": ["Hours", "Label : Year"],
                "mark_style": {
                    "mark-color": "#0070a0",
                    "size": "0.97751379013061523",
                    "has-stroke": "false",
                },
            }
        ],
        filters=filters,
    )
    e.configure_layered_chart(
        "BANs",
        columns=["Hours Axis", "Miles Axis", "Activities Axis"],
        axis_shelf="columns",
        fold_axes=False,
        panes=[
            {
                "axis": axis,
                "mark_type": "Text",
                "labels": [metric],
                "detail_extra": ["True", "False"],
                "label_runs": [
                    {
                        "field": metric,
                        "fontname": "Times New Roman",
                        "fontsize": 24,
                        "fontcolor": "#0070a0" if metric == "Hours" else "#333333",
                    },
                    {"text": "\n"},
                    {
                        "text": caption,
                        "fontname": "Times New Roman",
                        "fontsize": 10,
                        "fontcolor": "#898989",
                    },
                ],
                "mark_style": {"mark-labels-show": "true"},
            }
            for axis, metric, caption in [
                ("Hours Axis", "Hours", "HOURS"),
                ("Miles Axis", "Miles", "MILES"),
                ("Activities Axis", "# Actvities", "ACTIVITIES"),
            ]
        ],
        filters=filters,
    )
    for sheet in ["Calendar", "Weekly Profile", "BANs"]:
        e.configure_datasource_blend(
            sheet,
            secondary,
            {"BLEND: Date": "BLEND: Date"},
            ["SUM(Activity Hours)", "SUM(Miles)", "Activity Count"],
        )
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_table_dividers=sheet != "Calendar",
            hide_sort_controls=True,
        )
        e.set_worksheet_title(sheet, "")
    e.configure_worksheet_style(
        "Calendar",
        pane_formats=[{"attr": "background-color", "value": "#f5f5fa"}],
        label_formats=[
            {"field": f, "display": "false"} for f in ["Rows", "Cols", "DAY(Date)"]
        ],
        table_dividers=[
            {
                "scope": "rows",
                "stroke-size": 5,
                "stroke-color": "#ffffff",
                "div-level": 1,
            },
            {"scope": "cols", "stroke-size": 5, "stroke-color": "#ffffff"},
        ],
    )
    e.configure_worksheet_style(
        "Weekly Profile",
        label_formats=[{"field": "WEEK(BLEND: Date)", "display": "false"}],
    )
    e.configure_worksheet_style(
        "Calendar",
        axis_style={
            "encodings": [
                {
                    "field": "Monthly Summary Axis",
                    "attr": "space",
                    "class": 1,
                    "scope": "rows",
                    "type": "space",
                    "fold": False,
                },
                {
                    "field": "Hours",
                    "attr": "space",
                    "class": 0,
                    "scope": "rows",
                    "type": "space",
                    "fold": False,
                },
            ]
        },
    )
    e.configure_worksheet_style(
        "BANs",
        cell_formats=[
            {"field": field, "text-format": "n#,##0;-#,##0"}
            for field in ["Hours", "Miles"]
        ],
    )
    e.link_worksheet_filters(
        "YEAR(BLEND: Date)", ["Calendar", "Weekly Profile", "BANs"]
    )
    e.add_dashboard(
        DASHBOARD,
        width=1680,
        height=1020,
        layout={
            "type": "container",
            "direction": "vertical",
            "style": {"margin": 0},
            "children": [
                {
                    "type": "text",
                    "fixed_size": 56,
                    "text": "Training Calendar",
                    "runs": [
                        {
                            "text": "Training Calendar",
                            "font_size": 26,
                            "font_name": "Times New Roman",
                            "font_alignment": "0",
                            "bold": True,
                            "font_color": "#333333",
                        }
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 39,
                    "children": [
                        {
                            "type": "filter",
                            "worksheet": "Calendar",
                            "field": "YEAR(BLEND: Date)",
                            "mode": "slider",
                            "show_all": False,
                            "show_slider": False,
                            "show_title": False,
                            "values": "database",
                            "fixed_size": 205,
                        },
                        {"type": "empty"},
                    ],
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 109,
                    "children": [
                        {
                            "type": "worksheet",
                            "name": "Weekly Profile",
                            "fixed_size": 375,
                            "fit": "entire",
                            "show_title": False,
                        },
                        {"type": "empty", "fixed_size": 702},
                        {
                            "type": "worksheet",
                            "name": "BANs",
                            "fit": "entire",
                            "show_title": False,
                        },
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Calendar",
                    "fixed_size": 770,
                    "fit": "entire",
                    "show_title": False,
                    "style": {"margin": 0},
                },
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 46,
                    "children": [
                        {
                            "type": "text",
                            "text": "DESIGNED BY : ANDY KRIEBEL",
                            "font_size": 8,
                        },
                        {
                            "type": "text",
                            "text": "#WOW2020 | WEEK 42\nhttps://www.workout-wednesday.com/2020w42/",
                            "font_size": 8,
                        },
                        {
                            "type": "text",
                            "text": "RECREATED WITH CWTWB",
                            "font_size": 8,
                        },
                    ],
                },
            ],
        },
    )
    for sheet in ["Calendar", "Weekly Profile", "BANs"]:
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"True": "False"},
            event_type="on-select",
            caption="Unhighlight " + sheet,
        )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
