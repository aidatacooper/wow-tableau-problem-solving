"""Rebuild a fixed mobile calendar, parameter date selection and metric trend."""

from pathlib import Path
import re
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_09_23_WW39_Mobile_Calendar_Picker"
CALCULATIONS = [
    {
        "field_name": "COLOUR:Selected Month",
        "formula": "[pMonthSelected]=[Month Date]",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Month Date",
        "formula": "DATE(DATETRUNC('month',[Date]))\r\n//MAKEDATE([pYear],[pMonth],1)",
        "datatype": "date",
        "role": "dimension",
        "field_type": "quantitative",
    },
    {
        "field_name": "Month to Show",
        "formula": "[pMonthSelected] = [Month Date]",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Day of Week Abbrev",
        "formula": "LEFT(DATENAME('weekday', [Date]),3)",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "COLOUR : Date",
        "formula": "IF [Date]= [Date Selection Start] OR [Date] = [Date Selection End] THEN 'Hot Pink'\r\nELSEIF [Date] > [Date Selection Start] AND [Date] < [Date Selection End] THEN 'Pink'\r\nELSE 'White'\r\nEND",
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Date Control",
        "formula": 'IF [pSelectedDates]="" THEN STR([Date]) // If no selection then set to date selected via db action\r\nELSEIF CONTAINS([pSelectedDates],"|") THEN STR([Date]) // If begin and end selected then restart selection\r\nELSEIF [Date]<=DATE([pSelectedDates]) THEN  STR([Date]) // If no end date and end<begin then restart selection\r\nELSE [pSelectedDates]+"|"+STR([Date]) END // else store start & end date',
        "datatype": "string",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Date Selection Start",
        "formula": '//DATE(SPLIT([pSelectedDates], "|",1))\r\nDATE(LEFT([pSelectedDates],FIND([pSelectedDates],"|")-1))',
        "datatype": "date",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "field_name": "True",
        "formula": "True",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "False",
        "formula": "False",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Next Month",
        "formula": "IF [Month Date] = {MAX([Month Date])} THEN [Month Date] ELSE\r\nDATE(DATEADD('month', 1, [Month Date]))\r\nEND",
        "datatype": "date",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "field_name": "Dates to Show",
        "formula": "[Date]>= [Date Selection Start] AND [Date]<= [Date Selection End]",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "COLOUR:Selected Year",
        "formula": "YEAR([pMonthSelected])=YEAR([Date])",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Month Row",
        "formula": "IF DATEPART('month',[Date]) <=4 THEN 1\r\nELSEIF DATEPART('month',[Date]) <= 8 THEN 2\r\nELSE 3 END",
        "datatype": "integer",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "field_name": "Month Col",
        "formula": "IF (DATEPART('month',[Date]) %4) =0 THEN 4\r\nELSE (DATEPART('month',[Date]) %4)\r\nEND",
        "datatype": "integer",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "field_name": "Month No",
        "formula": "MONTH([Date])",
        "datatype": "integer",
        "role": "measure",
        "field_type": "quantitative",
    },
    {
        "field_name": "Filter Year",
        "formula": "YEAR([pMonthSelected]) = YEAR([Date])",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Filter Month",
        "formula": "DATENAME('month',[pMonthSelected])=DATENAME('month',[Date])",
        "datatype": "boolean",
        "role": "dimension",
        "field_type": "nominal",
    },
    {
        "field_name": "Date Selection End",
        "formula": 'DATE(MID([pSelectedDates], FIND([pSelectedDates],"|")+1,10))',
        "datatype": "date",
        "role": "dimension",
        "field_type": "ordinal",
    },
    {
        "field_name": "Prev Month",
        "formula": "IF [Month Date] = {MIN([Month Date])} THEN [Month Date] ELSE\r\nDATE(DATEADD('month', -1, [Month Date]))\r\nEnd",
        "datatype": "date",
        "role": "dimension",
        "field_type": "ordinal",
    },
]


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(
        str(next((HERE / "inputs").glob("*.hyper"))),
        tables=[
            {
                "name": "Dates",
                "table": "2020_09_23_WW39_Dates Table.csv_82C90693BAFC4B77810EE86B070F0258",
            },
            {"name": "Orders", "table": "Orders_324DE2998B434457B4CC3FCA80AF2C16"},
        ],
        relationships=[
            {"left": "Dates", "right": "Orders", "keys": [["Date", "Order Date"]]}
        ],
    )
    e.set_date_options(start_of_week="monday")
    e.add_parameter(
        "pMonthSelected",
        datatype="date",
        default_value="#2019-06-01#",
        domain_type="any",
    )
    e.add_parameter(
        "pSelectedDates",
        datatype="string",
        default_value="2019-06-06|2019-06-18",
        domain_type="any",
    )
    pending = {field["field_name"]: dict(field) for field in CALCULATIONS}
    for field in pending.values():
        field["formula"] = re.sub(r"//[^\r\n]*", "", field["formula"])
    while pending:
        ready = [
            name
            for name, field in pending.items()
            if not (set(re.findall(r"\[([^\]]+)\]", field["formula"])) & set(pending))
        ]
        if not ready:
            raise ValueError(f"Calculation cycle: {list(pending)}")
        for name in ready:
            e.add_calculated_field(**pending.pop(name))
    e.add_calculated_field("Calendar Axis", "MIN(1)")
    e.add_calculated_field("Year Axis", "MIN(1)")
    e.add_calculated_field("Month Axis", "MIN(1)")
    e.add_calculated_field(
        "Weekday Sort",
        "MIN(CASE [Day of Week Abbrev] WHEN 'Mon' THEN 7 WHEN 'Tue' THEN 6 WHEN 'Wed' THEN 5 WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 3 WHEN 'Sat' THEN 2 ELSE 1 END)",
    )
    e.set_datasource_color_palette(
        "COLOUR : Date", {"Hot Pink": "#f94786", "Pink": "#ffe0ed", "White": "#ffffff"}
    )
    for field in ["COLOUR:Selected Year", "COLOUR:Selected Month"]:
        e.set_datasource_color_palette(field, {True: "#f94786", False: "#ffffff"})
    for metric in ["Sales", "Profit"]:
        e.set_field_format(metric, "n0.###############;-0.###############")
    e.set_field_format("Quantity", "n#,##0;-#,##0")
    for sheet in [
        "Calendar",
        "BAN",
        "Line ",
        "Month",
        "Month Name",
        "Next Month Control",
        "Prev Month Control",
        "Selected Period",
        "Year",
    ]:
        e.add_worksheet(sheet)
    e.configure_layered_chart(
        "Calendar",
        axis_shelf="columns",
        rows=["WEEK(Date)"],
        columns=["Day of Week Abbrev", "Calendar Axis"],
        panes=[
            {
                "axis": "Calendar Axis",
                "mark_type": "Bar",
                "color": "COLOUR : Date",
                "labels": ["DAY(Date)"],
                "detail": "Date",
                "detail_extra": ["True", "False"],
                "tooltip": ["ATTR(Date Control)", "Date Selection Start"],
                "mark_sizing_off": True,
                "label_runs": [{"field": "DAY(Date)", "fontsize": 8}],
                "mark_style": {
                    "size": "1.9890055656433105",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
            }
        ],
        filters=[{"column": "Month to Show", "values": [True]}],
        sort_field="Day of Week Abbrev",
        sort_descending="Weekday Sort",
    )
    e.configure_layered_chart(
        "BAN",
        rows=["Measure Names"],
        panes=[
            {
                "mark_type": "Bar",
                "mark_style": {
                    "mark-color": "#ffffff",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                },
                "labels": ["Multiple Values", "Measure Names"],
                "label": "Multiple Values",
                "measure_values": ["SUM(Sales)", "SUM(Profit)", "SUM(Quantity)"],
                "label_runs": [
                    {"field": "Multiple Values", "fontsize": 14, "bold": True},
                    {"text": "\n"},
                    {"field": "Measure Names", "fontsize": 9},
                ],
            }
        ],
        filters=[{"column": "Dates to Show", "values": [True]}],
    )
    e.configure_layered_chart(
        "Line ",
        columns=["EXACTDATE(Date)"],
        rows=["SUM(Sales)", "SUM(Profit)", "SUM(Quantity)"],
        panes=[
            {
                "axis": f"SUM({metric})",
                "mark_type": "Line",
                "mark_style": {"mark-color": "#f94786", "size": "0.6"},
            }
            for metric in ["Sales", "Profit", "Quantity"]
        ],
        axis_shelf="rows",
        fold_axes=False,
        filters=[{"column": "Dates to Show", "values": [True]}],
    )
    e.configure_chart(
        "Month Name",
        mark_type="Text",
        label_runs=[{"field": "MIN(Month Date)", "fontsize": 8, "bold": True}],
        label_extra=["MIN(Month Date)"],
        filters=[{"column": "Month to Show", "values": [True]}],
    )
    e.configure_layered_chart(
        "Selected Period",
        panes=[
            {
                "mark_type": "Text",
                "labels": ["MIN(Date Selection Start)", "MIN(Date Selection End)"],
                "label_runs": [
                    {"text": "Selected Period: ", "bold": True, "fontsize": 8},
                    {"field": "MIN(Date Selection Start)", "fontsize": 8},
                    {"text": " - ", "fontsize": 8},
                    {"field": "MIN(Date Selection End)", "fontsize": 8},
                ],
                "mark_style": {"mark-labels-show": "true", "mark-labels-cull": "false"},
            }
        ],
    )
    e.add_calculated_field(
        "Navigation Direction",
        "'\u276f'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Previous Direction",
        "'\u276e'",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    for sheet, field, shape in [
        ("Next Month Control", "Next Month", "Navigation Direction"),
        ("Prev Month Control", "Prev Month", "Previous Direction"),
    ]:
        e.configure_layered_chart(
            sheet,
            panes=[
                {
                    "mark_type": "Text",
                    "labels": [shape],
                    "label_runs": [
                        {"field": shape, "fontsize": 18, "fontcolor": "#818b91"}
                    ],
                    "detail": f"MIN({field})",
                    "mark_sizing_off": True,
                    "mark_style": {
                        "size": "2",
                        "mark-color": "#818b91",
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                    },
                }
            ],
            filters=[{"column": "Month to Show", "values": [True]}],
        )
    e.configure_layered_chart(
        "Year",
        columns=["YEAR(Date)"],
        rows=["Year Axis"],
        panes=[
            {
                "axis": "Year Axis",
                "mark_type": "Bar",
                "color": "COLOUR:Selected Year",
                "labels": ["YEAR(Date)"],
                "detail": "MIN(Month Date)",
                "detail_extra": ["True", "False"],
                "label_runs": [{"field": "YEAR(Date)", "fontsize": 10}],
                "mark_style": {"size": "1", "mark-labels-show": "true"},
            }
        ],
        filters=[{"column": "Filter Month", "values": [True]}],
    )
    e.configure_layered_chart(
        "Month",
        columns=["Month Col"],
        rows=["Month Row", "Month Axis"],
        panes=[
            {
                "axis": "Month Axis",
                "mark_type": "Bar",
                "color": "COLOUR:Selected Month",
                "labels": ["MONTH(Date)"],
                "detail": "MIN(Month Date)",
                "detail_extra": ["True", "False"],
                "label_runs": [{"field": "MONTH(Date)", "fontsize": 10}],
                "mark_style": {"size": "1", "mark-labels-show": "true"},
            }
        ],
        filters=[{"column": "Filter Year", "values": [True]}],
    )
    for sheet in [
        "Calendar",
        "BAN",
        "Line ",
        "Month",
        "Month Name",
        "Next Month Control",
        "Prev Month Control",
        "Selected Period",
        "Year",
    ]:
        e.configure_worksheet_style(
            sheet,
            hide_axes=sheet != "Line ",
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
            pane_datalabel_style={"font-size": 9, "color-mode": "auto"},
            pane_cell_style={"text-align": "center", "vertical-align": "center"},
            cell_formats=[{"height": 36}],
        )
    e.configure_worksheet_style(
        "Calendar",
        hide_row_label="WEEK(Date)",
        axis_style={
            "per_field": [
                {
                    "field": "Calendar Axis",
                    "scope": "cols",
                    "class": 0,
                    "attr": "range-type",
                    "value": "fixed",
                }
            ],
            "encodings": [
                {
                    "field": "Calendar Axis",
                    "scope": "cols",
                    "class": 0,
                    "type": "space",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                }
            ],
        },
        header_formats=[{"field": "Day of Week Abbrev", "font-size": 9}],
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
    )
    e.configure_worksheet_style(
        "BAN", header_formats=[{"field": "Measure Names", "display": "false"}]
    )
    e.configure_worksheet_style(
        "Month Name",
        cell_formats=[{"field": "MIN(Month Date)", "text-format": "*mmm yyyy"}],
    )
    e.configure_worksheet_style(
        "Selected Period",
        cell_formats=[
            {"field": f"MIN({field})", "text-format": "*dd mmm yyyy"}
            for field in ["Date Selection Start", "Date Selection End"]
        ],
    )
    e.configure_worksheet_style(
        "Year", header_formats=[{"field": "YEAR(Date)", "display": "false"}]
    )
    e.configure_worksheet_style(
        "Month",
        hide_row_label="Month Row",
        header_formats=[{"field": "Month Col", "display": "false"}],
        cell_formats=[{"field": "MONTH(Date)", "text-format": "iMMM"}],
    )
    e.configure_worksheet_style(
        "Line ",
        label_formats=[
            {"field": f"SUM({metric})", "font-size": 8}
            for metric in ["Sales", "Profit", "Quantity"]
        ],
        axis_style={
            "per_field": [
                {
                    "field": f"SUM({metric})",
                    "scope": "rows",
                    "class": 0,
                    "attr": "title",
                    "value": "",
                }
                for metric in ["Sales", "Profit", "Quantity"]
            ]
            + [
                {
                    "field": "EXACTDATE(Date)",
                    "scope": "cols",
                    "class": 0,
                    "attr": "display",
                    "value": "false",
                }
            ]
        },
    )

    def zone(kind, x, y, w, h, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 350 * 100000),
                "y": round(y / 700 * 100000),
                "w": round(w / 350 * 100000),
                "h": round(h / 700 * 100000),
            },
            "style": {"margin": 4},
            **kwargs,
        }

    zones = [
        zone(
            "text",
            8,
            8,
            334,
            33,
            runs=[{"text": "Mobile Calendar Picker", "font_size": 15, "bold": True}],
        ),
        zone(
            "worksheet",
            8,
            41,
            84,
            33,
            name="Month Name",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            175,
            41,
            84,
            33,
            name="Prev Month Control",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            259,
            41,
            42,
            33,
            name="Next Month Control",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            8,
            74,
            334,
            270,
            name="Calendar",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            8,
            344,
            334,
            35,
            name="Selected Period",
            fit="entire",
            show_title=False,
        ),
        zone(
            "text",
            8,
            379,
            334,
            29,
            runs=[
                {
                    "text": "Sales, Profit and Quantity for selected dates",
                    "font_size": 9,
                }
            ],
        ),
        zone("worksheet", 8, 408, 113, 207, name="BAN", fit="entire", show_title=False),
        zone(
            "worksheet",
            121,
            408,
            221,
            207,
            name="Line ",
            fit="entire",
            show_title=False,
        ),
        zone(
            "text",
            8,
            615,
            334,
            45,
            runs=[
                {
                    "text": "#WOW2020 | WEEK 39  /  Recreated by Donna Coles",
                    "font_size": 7,
                }
            ],
        ),
        zone(
            "text",
            8,
            660,
            334,
            32,
            runs=[{"text": "workout-wednesday.com/2020w39/", "font_size": 8}],
        ),
        zone(
            "container",
            6,
            101,
            337,
            243,
            direction="vertical",
            style={"margin": 0, "background-color": "#ffffff"},
            children=[
                {
                    "type": "worksheet",
                    "name": "Year",
                    "fit": "entire",
                    "show_title": False,
                    "fixed_size": 79,
                    "style": {"margin": 4},
                },
                {
                    "type": "worksheet",
                    "name": "Month",
                    "fit": "entire",
                    "show_title": False,
                    "fixed_size": 164,
                    "style": {"margin": 4},
                },
            ],
        ),
    ]
    e.add_dashboard(
        DASHBOARD,
        width=350,
        height=700,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": zones,
        },
    )
    e.add_dashboard_toggle_button(
        DASHBOARD,
        ["Year", "Month"],
        caption_shown="Hide",
        caption_hidden="Month",
        initially_hidden=True,
        position={"x": 300, "y": 41, "w": 42, "h": 33},
    )
    for caption, sheet, field, target in [
        ("Set dates", "Calendar", "ATTR(Date Control)", "pSelectedDates"),
        ("Next month", "Next Month Control", "MIN(Next Month)", "pMonthSelected"),
        ("Previous month", "Prev Month Control", "MIN(Prev Month)", "pMonthSelected"),
        ("Select year", "Year", "MIN(Month Date)", "pMonthSelected"),
        ("Select month", "Month", "MIN(Month Date)", "pMonthSelected"),
    ]:
        e.add_dashboard_action(
            DASHBOARD,
            "parameter",
            source_sheet=sheet,
            source_field=field,
            target_parameter=target,
            event_type="on-select",
            caption=caption,
            aggregation="attr",
        )
    for sheet in ["Calendar", "Year", "Month"]:
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"True": "False"},
            caption=sheet + " deselect",
            event_type="on-select",
        )
    e.configure_worksheet_style(
        "BAN",
        hide_row_label="Measure Names",
        cell_formats=[{"width": 110}]
        + [
            {"field": f"SUM({metric})", "text-format": 'c"$"#,##0;-"$"#,##0'}
            for metric in ["Sales", "Profit"]
        ],
        table_formats=[{"attr": "band-color", "value": "#ffffff", "scope": "rows"}],
    )
    e.configure_worksheet_style(
        "Calendar", cell_formats=[{"field": "WEEK(Date)", "height": 52}]
    )
    e.configure_worksheet_style(
        "Line ",
        table_formats=[
            {"attr": a, "value": v}
            for a, v in [
                ("omit-on-special", "false"),
                ("break-on-special", "false"),
                ("alternate-text", "0"),
                ("display-alternate-text", "true"),
                ("show-null-value-warning", "false"),
            ]
        ],
    )
    e.copy_default_device_layout(DASHBOARD, device_name="Phone")
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
