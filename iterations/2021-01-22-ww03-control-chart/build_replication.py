"""Build control-chart summary and detail from locked Hyper using public SDK."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
SUMMARY = "2021_01_20_WW03_Control_Chart_Summary"
DETAIL = "2021_01_20_WW03_Control_Chart_Detail"
PARAMETERS = ["Select a Date", "Latest X Years", "STD"]


def pixel_rect(x, y, width, height):
    """Declarative layout absolute rectangles use normalized Tableau coordinates."""
    return {
        "x": round(x / 900 * 100000),
        "y": round(y / 700 * 100000),
        "w": round(width / 900 * 100000),
        "h": round(height / 700 * 100000),
    }


def summary_layout(main):
    """Keep chart layout fixed while the parameter panel is an independent peer."""
    panel = main["children"].pop()
    panel["absolute"] = pixel_rect(707, 33, 184, 233)
    main["absolute"] = {"x": 0, "y": 0, "w": 100000, "h": 100000}
    return {"type": "container", "direction": "floating", "children": [main, panel]}


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs/consumer-complaints.hyper"))
    e.set_date_options(start_of_week="monday")
    e.add_parameter(
        "Select a Date",
        datatype="string",
        default_value="Date Submitted",
        domain_type="list",
        allowed_values=["Date Submitted", "Date Received"],
    )
    for name, value, maximum in [("Latest X Years", "3", "5"), ("STD", "1", "3")]:
        e.add_parameter(
            name,
            datatype="integer",
            default_value=value,
            domain_type="range",
            min_value="1",
            max_value=maximum,
            granularity="1",
        )
    definitions = [
        (
            "Date to Plot",
            "DATE(DATETRUNC('week', IIF([Select a Date]='Date Submitted',[Date sent to company], [Date received])))",
            "date",
            "dimension",
            "ordinal",
            None,
        ),
        (
            "Year of Latest Date",
            "YEAR({MAX([Date to Plot])})",
            "integer",
            "dimension",
            "ordinal",
            None,
        ),
        (
            "Dates to Include",
            "[Date to Plot]>=MAKEDATE([Year of Latest Date]-([Latest X Years]-1),1,1)",
            "boolean",
            "dimension",
            "nominal",
            None,
        ),
        ("Date From", "[Date to Plot]", "date", "dimension", "ordinal", None),
        (
            "Date To",
            "DATE(DATEADD('day',6,[Date to Plot]))",
            "date",
            "dimension",
            "ordinal",
            None,
        ),
        ("Year", "YEAR([Date to Plot])", "integer", "dimension", "ordinal", None),
        (
            "Week Number",
            "DATEPART('week',[Date to Plot])",
            "integer",
            "dimension",
            "ordinal",
            None,
        ),
        ("Dummy", "'DUMMY'", "string", "dimension", "nominal", None),
        (
            "Number of Complaints",
            "COUNT([Complaint ID])",
            "integer",
            "measure",
            "quantitative",
            None,
        ),
        (
            "Avg Complaints Per Year",
            "WINDOW_AVG([Number of Complaints])",
            "real",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Upper Limit",
            "[Avg Complaints Per Year]+WINDOW_STDEV([Number of Complaints])*[STD]",
            "real",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Lower Limit",
            "[Avg Complaints Per Year]-WINDOW_STDEV([Number of Complaints])*[STD]",
            "real",
            "measure",
            "quantitative",
            "Rows",
        ),
        (
            "Within STD Limits?",
            "[Number of Complaints]<[Upper Limit] AND [Number of Complaints]>[Lower Limit]",
            "boolean",
            "measure",
            "nominal",
            "Rows",
        ),
        (
            "In or Out of Upper or Lower Limits?",
            "IF [Within STD Limits?] THEN 'In' ELSE 'Out' END",
            "string",
            "measure",
            "nominal",
            "Rows",
        ),
        (
            "Received Week",
            "DATE(DATETRUNC('week',[Date received]))",
            "date",
            "dimension",
            "ordinal",
            None,
        ),
        (
            "Submitted Week",
            "DATE(DATETRUNC('week',[Date sent to company]))",
            "date",
            "dimension",
            "ordinal",
            None,
        ),
        (
            "Response Header",
            "'Company response to consumer'",
            "string",
            "dimension",
            "nominal",
            None,
        ),
        (
            "Dynamic Subtitle",
            "'Over the last '+STR([Latest X Years])+' years by week of '+[Select a Date]+'. Showing +/- '+STR([STD])+' standard deviations'",
            "string",
            "dimension",
            "nominal",
            None,
        ),
    ]
    for name, formula, datatype, role, kind, tc in definitions:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind, table_calc=tc
        )
    e.set_field_format("Date to Plot", "*dd mmmm yyyy")
    for name in ["Date From", "Date To"]:
        e.set_field_format(name, "*dd/mm/yyyy")
    for name in ["Avg Complaints Per Year", "Lower Limit", "Upper Limit"]:
        e.set_field_format(name, "n#,##0.00;-#,##0.00")
    filters = [{"column": "Dates to Include", "values": [True]}]
    e.add_worksheet("Chart")
    weekly = {"ordering_type": "Field", "ordering_field": "Week Number"}
    overrides = {
        "Avg Complaints Per Year": [weekly],
        "Upper Limit": [weekly, {**weekly, "field": "Avg Complaints Per Year"}],
        "Lower Limit": [weekly, {**weekly, "field": "Avg Complaints Per Year"}],
        "Within STD Limits?": [
            weekly,
            {**weekly, "field": "Upper Limit"},
            {**weekly, "field": "Avg Complaints Per Year"},
            {**weekly, "field": "Lower Limit"},
        ],
        "In or Out of Upper or Lower Limits?": [
            weekly,
            {**weekly, "field": "Within STD Limits?"},
            {**weekly, "field": "Upper Limit"},
            {**weekly, "field": "Avg Complaints Per Year"},
            {**weekly, "field": "Lower Limit"},
        ],
    }
    # Preserve the original Chart's nested AVG Rows context. It intentionally
    # differs from the yearly mean of the band and auxiliary Data worksheet.
    overrides["Within STD Limits?"] = [
        {"ordering_type": "Rows"},
        {**weekly, "field": "Upper Limit"},
        {"ordering_type": "Rows", "field": "Avg Complaints Per Year"},
        {**weekly, "field": "Lower Limit"},
    ]
    overrides["In or Out of Upper or Lower Limits?"] = [
        {"ordering_type": "Rows"},
        {"ordering_type": "Rows", "field": "Within STD Limits?"},
        {**weekly, "field": "Upper Limit"},
        {"ordering_type": "Rows", "field": "Avg Complaints Per Year"},
        {**weekly, "field": "Lower Limit"},
    ]
    common = {
        "axis": "Number of Complaints",
        "detail_extra": [
            "Avg Complaints Per Year",
            "Upper Limit",
            "Lower Limit",
            "Dummy",
        ],
        "tooltip": [
            "ATTR(Date to Plot)",
            "ATTR(Date From)",
            "ATTR(Date To)",
            "In or Out of Upper or Lower Limits?",
        ],
    }
    e.configure_layered_chart(
        "Chart",
        columns=["Year", "Week Number"],
        rows=["Number of Complaints", "Number of Complaints"],
        panes=[
            {
                **common,
                "mark_type": "Line",
                "labels": ["Number of Complaints"],
                "mark_style": {
                    "size": "0.29585635662078857",
                    "mark-color": "#898989",
                    "mark-labels-show": "true",
                    "mark-labels-mode": "range",
                    "mark-labels-cull": "false",
                },
                "datalabel_style": {"font-size": "8"},
            },
            {
                **common,
                "mark_type": "Circle",
                "color": "Within STD Limits?",
                "color_map": {True: "#767f8b", False: "#f28e2b"},
                "mark_style": {
                    "size": "1.2193922996520996",
                    "mark-labels-show": "false",
                },
            },
        ],
        filters=filters,
        table_calc_overrides=overrides,
    )
    e.add_reference_band(
        "Chart",
        axis_field="Number of Complaints",
        lower_field="Lower Limit",
        upper_field="Upper Limit",
        fill_color="#f5f5f5",
        pane_index=0,
    )
    for i in [0, 1]:
        e.configure_reference_line_style(
            "Chart", f"refline{i}", {"line-visibility": "off", "stroke-size": 0}
        )
    tooltip = [
        {"field": "ATTR(Date to Plot)", "bold": True},
        {"text": "\nNumber of Complaints: ", "fontsize": 8},
        {"field": "Number of Complaints", "bold": True, "fontsize": 8},
        {"text": "\nDate Range: ", "fontsize": 8},
        {"field": "ATTR(Date From)", "bold": True, "fontsize": 8},
        {"text": " - "},
        {"field": "ATTR(Date To)", "bold": True, "fontsize": 8},
        {"text": "\nIn or Out of Upper or Lower Limits? ", "fontsize": 8},
        {"field": "In or Out of Upper or Lower Limits?", "bold": True, "fontsize": 8},
        {"text": "\n(LL ", "italic": True, "fontsize": 8},
        {"field": "Lower Limit", "fontsize": 8},
        {"text": " - UL ", "fontsize": 8},
        {"field": "Upper Limit", "fontsize": 8},
        {"text": ")", "fontsize": 8},
    ]
    for i in [0, 1]:
        e.configure_custom_tooltip("Chart", tooltip, pane_index=i)
    e.configure_worksheet_style(
        "Chart",
        hide_axes=True,
        hide_col_field_labels=True,
        hide_sort_controls=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_zeroline=True,
        axis_style={
            "encodings": [
                {
                    "field": "Number of Complaints",
                    "attr": "space",
                    "scope": "rows",
                    "class": 0,
                    "type": "space",
                    "major-origin": 0,
                    "major-spacing": 100,
                }
            ]
        },
        gridline_style={
            "rows": {
                "line-visibility": "on",
                "line-pattern": "solid",
                "stroke-size": 1,
            },
            "cols": {"line-visibility": "off"},
        },
        label_formats=[{"field": "Week Number", "display": "false"}],
        header_formats=[
            {"height-header": "22"},
            {"field": "Year", "height": "42", "font-size": "8"},
        ],
    )
    e.set_worksheet_title("Chart", "")
    e.add_worksheet("Heading")
    e.configure_chart("Heading", mark_type="Text", label="Dynamic Subtitle")
    e.configure_custom_label(
        "Heading",
        [
            {"text": "Can you create a Control Chart?\n", "fontsize": 16},
            {"text": "Number of Complaints\n", "fontsize": 12},
            {"field": "Dynamic Subtitle", "fontsize": 10, "italic": True},
            {
                "text": "\nClick a mark to take you to Complaint Details",
                "fontsize": 10,
                "italic": True,
                "fontcolor": "#3b54a7",
            },
        ],
    )
    e.configure_worksheet_style(
        "Heading",
        hide_axes=True,
        hide_borders=True,
        hide_gridlines=True,
        hide_zeroline=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "left", "vertical-align": "top"},
    )
    e.set_worksheet_title("Heading", "")
    e.add_worksheet("Data")
    e.configure_layered_chart(
        "Data",
        rows=["Year", "[Date From]", "[Date To]", "Within STD Limits?"],
        columns=["Measure Names"],
        panes=[
            {
                "mark_type": "Text",
                "label": "Multiple Values",
                "measure_values": [
                    "Number of Complaints",
                    "Avg Complaints Per Year",
                    "Upper Limit",
                    "Lower Limit",
                ],
            }
        ],
        filters=filters,
        table_calc_overrides={
            k: [
                {"ordering_type": "Field", "order": ["[Date From]", "[Date To]"]},
                *[
                    {
                        "ordering_type": "Field",
                        "order": ["[Date From]", "[Date To]"],
                        "field": v["field"],
                    }
                    for v in vals
                    if "field" in v
                ],
            ]
            for k, vals in overrides.items()
            if k != "In or Out of Upper or Lower Limits?"
        },
    )
    e.add_worksheet("Detail")
    e.configure_chart(
        "Detail",
        mark_type="Text",
        rows=[
            "Year",
            "Week Number",
            "Dummy",
            "Timely response?",
            "[Complaint ID]",
            "[Date to Plot]",
            "[Received Week]",
            "[Submitted Week]",
            "State",
            "Submitted via",
            "Product",
            "Issue",
        ],
        columns=["Response Header"],
        label="Company response to consumer",
        filters=filters,
    )
    e.configure_worksheet_style(
        "Detail",
        hide_col_field_labels=True,
        hide_sort_controls=True,
        hide_gridlines=True,
        hide_zeroline=True,
        label_formats=[
            {"field": f, "display": "false"}
            for f in ["Year", "Week Number", "Dummy", "[Date to Plot]"]
        ],
        pane_cell_style={"text-align": "left", "font-size": "8"},
    )
    e.set_worksheet_rich_title(
        "Detail",
        [
            {
                "text": "Complaint Details | Week of <[Parameters].[Select a Date]> - <[Date to Plot]>",
                "fontsize": 12,
            }
        ],
    )
    e.add_dashboard(
        SUMMARY,
        width=900,
        height=700,
        layout=summary_layout(
            {
                "type": "container",
                "style": {"margin": 8},
                "children": [
                    {
                        "type": "worksheet",
                        "name": "Heading",
                        "show_title": False,
                        "fixed_size": 96,
                        "fit": "entire",
                    },
                    {
                        "type": "worksheet",
                        "name": "Chart",
                        "show_title": False,
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
                                        "text": "CHALLENGE BY : LORNA BROWN",
                                        "font_size": 8,
                                        "font_color": "#79706e",
                                        "bold": True,
                                        "font_alignment": "0",
                                    }
                                ],
                            },
                            {
                                "type": "text",
                                "runs": [
                                    {
                                        "text": "#WOW2021 | WEEK 3",
                                        "font_size": 8,
                                        "font_color": "#79706e",
                                        "bold": True,
                                        "font_alignment": "1",
                                    }
                                ],
                            },
                            {
                                "type": "text",
                                "runs": [
                                    {
                                        "text": "RECREATED WITH CWTWB",
                                        "font_size": 8,
                                        "font_color": "#79706e",
                                        "bold": True,
                                        "font_alignment": "2",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "type": "text",
                        "runs": [
                            {
                                "text": "https://www.workout-wednesday.com/2021w03tab/",
                                "font_size": 8,
                                "font_alignment": "1",
                                "hyperlink": "https://www.workout-wednesday.com/2021w03tab/",
                            }
                        ],
                        "fixed_size": 32,
                    },
                    {
                        "type": "container",
                        "direction": "vertical",
                        "absolute": {"x": 707, "y": 33, "w": 184, "h": 233},
                        "style": {"background-color": "#ffffff"},
                        "children": [
                            {
                                "type": "paramctrl",
                                "parameter": name,
                                "mode": "list" if name == "Select a Date" else "slider",
                            }
                            for name in PARAMETERS
                        ],
                    },
                ],
            }
        ),
    )
    e.add_dashboard_toggle_button(
        SUMMARY,
        target_parameters=PARAMETERS,
        initially_hidden=True,
        caption_shown="Hide Controls",
        caption_hidden="Show Controls",
        position={"x": 763, "y": 8, "w": 131, "h": 27},
    )
    # Source detail uses a full-size sheet and a small floating Back button.
    e.add_dashboard(
        DETAIL,
        width=900,
        height=700,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": [
                {
                    "type": "worksheet",
                    "name": "Detail",
                    "fit": "width",
                    "absolute": pixel_rect(8, 8, 884, 684),
                },
                {
                    "type": "navigation_button",
                    "target_dashboard": SUMMARY,
                    "caption": "Back",
                    "font_color": "#ffffff",
                    "background_color": "#998f8c",
                    "absolute": pixel_rect(783, 12, 112, 23),
                },
            ],
        },
    )
    e.add_dashboard_action(
        SUMMARY,
        "filter",
        source_sheet="Chart",
        target_sheet="Detail",
        target_dashboard=DETAIL,
        fields=["Year", "Week Number", "Dummy"],
        clear_behavior="show-none",
        caption="Click to Show Details",
    )
    e.initialize_dashboard_filter_action(
        SUMMARY,
        "Click to Show Details",
        {"Year": [0], "Week Number": [0], "Dummy": ["NO_SELECTION"]},
    )
    e.add_dashboard_action(
        SUMMARY,
        "highlight",
        source_sheet="Chart",
        target_sheet="Chart",
        fields=["Dummy"],
        caption="Highlight Dummy",
    )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
