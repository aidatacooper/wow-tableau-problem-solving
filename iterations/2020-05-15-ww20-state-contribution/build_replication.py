"""Native filled map, selected-state set add/remove actions and contributions."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_05_13_WW20_Remove_Set_Actions"
INITIAL_STATES = ["Alabama", "Illinois", "Kentucky", "Virginia"]


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(HERE / "inputs/Orders (Sample - Superstore).hyper"))
    editor.set_field_geographic_role("State", "state")
    editor.set_geocoding_context(country="United States")
    editor.add_set("Selected States", "State", members=INITIAL_STATES)
    for name, formula, datatype, role, kind in [
        ("True", "TRUE", "boolean", "dimension", "nominal"),
        ("False", "FALSE", "boolean", "dimension", "nominal"),
        ("Show Selected State", "[Selected States]", "boolean", "dimension", "nominal"),
        ("# Orders", "COUNTD([Order ID])", "integer", "measure", "quantitative"),
        ("# Customers", "COUNTD([Customer ID])", "integer", "measure", "quantitative"),
        ("Total Sales", "{FIXED:SUM([Sales])}", "real", "measure", "quantitative"),
        (
            "Total Orders",
            "{FIXED:COUNTD([Order ID])}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Total Customers",
            "{FIXED:COUNTD([Customer ID])}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Sales of Selected States",
            "{FIXED:SUM(IF [Selected States] THEN [Sales] END)}",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Orders of Selected States",
            "{FIXED:COUNTD(IF [Selected States] THEN [Order ID] END)}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Customers of Selected States",
            "{FIXED:COUNTD(IF [Selected States] THEN [Customer ID] END)}",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "% Sales of Selected States",
            "[Sales of Selected States]/[Total Sales]",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "% Orders of Selected States",
            "[Orders of Selected States]/[Total Orders]",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "% Customers of Selected States",
            "[Customers of Selected States]/[Total Customers]",
            "real",
            "measure",
            "quantitative",
        ),
        ("One", "1.0", "real", "measure", "quantitative"),
        (
            "Selection Order",
            "IF [Selected States] THEN 0 ELSE 1 END",
            "integer",
            "measure",
            "quantitative",
        ),
        ("State Label", "'x '+[State]", "string", "dimension", "nominal"),
    ]:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    for name, formula in [
        (
            "Sales Heading",
            "STR(ROUND(MIN([% Sales of Selected States])*100,1))+'% of $'+STR(ROUND(MIN([Total Sales])/1000000,2))+'M in total sales'",
        ),
        (
            "Orders Heading",
            "STR(ROUND(MIN([% Orders of Selected States])*100,1))+'% of '+STR(INT(MIN([Total Orders])))+' total orders'",
        ),
        (
            "Customers Heading",
            "STR(ROUND(MIN([% Customers of Selected States])*100,1))+'% of '+STR(INT(MIN([Total Customers])))+' total customers'",
        ),
    ]:
        editor.add_calculated_field(
            name, formula, datatype="string", role="measure", field_type="nominal"
        )
    colors = {"true": "#7c00b2", "false": "#d4d4d4"}
    editor.add_worksheet("Map")
    editor.configure_layered_chart(
        "Map",
        columns=["Longitude (generated)"],
        rows=["Latitude (generated)"],
        panes=[
            {
                "axis": "Latitude (generated)",
                "mark_type": "Multipolygon",
                "geometry": "Geometry (generated)",
                "detail": "State",
                "color": "Selected States",
                "color_map": colors,
                "detail_extra": ["True", "False"],
                "tooltip": ["SUM(Sales)", "# Orders", "# Customers"],
                "selection_relaxation": "disallow",
            }
        ],
    )
    editor.configure_worksheet_style(
        "Map",
        hide_axes=True,
        hide_borders=True,
        map_style={"washout": "1.0"},
        pane_mark_style={"mark-color": "#d4d4d4", "mark-transparency": "100"},
    )
    for sheet, measure in [("Sales", "SUM([Sales])"), ("Orders", "[# Orders]")]:
        share = sheet + " Contribution"
        editor.add_calculated_field(
            share, measure + "/WINDOW_SUM(" + measure + ")", table_calc="Rows"
        )
        editor.set_field_format(share, "p0.0%")
        editor.add_worksheet(sheet)
        editor.configure_layered_chart(
            sheet,
            columns=[share],
            rows=[],
            axis_shelf="columns",
            panes=[
                {
                    "axis": share,
                    "mark_type": "Bar",
                    "color": "Selected States",
                    "color_map": colors,
                    "detail_extra": [
                        "MIN(Total " + sheet + ")",
                        "MIN(% " + sheet + " of Selected States)",
                        "MIN(" + sheet + " of Selected States)",
                        sheet + " Heading",
                    ],
                }
            ],
            sort_field="Selected States",
            sort_descending="MIN(Selection Order)",
            table_calc_overrides={
                share: [{"ordering_type": "Field", "ordering_field": "Selected States"}]
            },
        )
        editor.configure_worksheet_style(
            sheet,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_sort_controls=True,
            pane_cell_style={"font-size": "8"},
            pane_mark_style={"size": "0.8", "mark-labels-show": "false"},
            axis_style={
                "encodings": [
                    {
                        "field": share,
                        "attr": "space",
                        "type": "space",
                        "scope": "cols",
                        "field-type": "quantitative",
                        "min": "0",
                        "max": "1",
                        "range-type": "fixed",
                    }
                ],
                "per_field": [
                    {"field": share, "attr": "title", "scope": "cols", "value": ""}
                ],
            },
            label_formats=[{"field": share, "text-format": "p0%"}],
        )
        editor.set_worksheet_rich_title(
            sheet, [{"text": "<" + sheet + " Heading>", "fontsize": 10}]
        )
    editor.set_field_format("% Customers of Selected States", "p0.0%")
    editor.set_field_format("One", "p0%")
    editor.add_worksheet("Customers")
    editor.configure_layered_chart(
        "Customers",
        columns=["MIN(% Customers of Selected States)", "MIN(One)"],
        rows=[],
        axis_shelf="columns",
        fold_axes=True,
        panes=[
            {
                "axis": "MIN(% Customers of Selected States)",
                "mark_type": "Bar",
                "detail_extra": [
                    "MIN(Total Customers)",
                    "MIN(Customers of Selected States)",
                    "Customers Heading",
                ],
                "mark_style": {
                    "mark-color": "#7c00b2",
                    "size": "0.8",
                    "mark-labels-show": "false",
                },
                "selection_relaxation": "disallow",
            },
            {
                "axis": "MIN(One)",
                "mark_type": "Bar",
                "detail_extra": [
                    "MIN(Total Customers)",
                    "MIN(Customers of Selected States)",
                    "Customers Heading",
                ],
                "mark_style": {
                    "mark-color": "#d4d4d4",
                    "size": "0.8",
                    "mark-labels-show": "false",
                },
                "selection_relaxation": "disallow",
            },
        ],
    )
    editor.configure_worksheet_style(
        "Customers",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_sort_controls=True,
        pane_cell_style={"font-size": "8"},
        label_formats=[
            {"field": "MIN(% Customers of Selected States)", "text-format": "p0%"}
        ],
        axis_style={
            "render-fold-reversed": "true",
            "encodings": [
                {
                    "field": field,
                    "attr": "space",
                    "type": "space",
                    "scope": "cols",
                    "field-type": "quantitative",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                }
                for field in ["MIN(One)", "MIN(% Customers of Selected States)"]
            ],
            "per_field": [
                {"field": "MIN(One)", "attr": "height", "value": "32", "class": "0"},
                {
                    "field": "MIN(% Customers of Selected States)",
                    "attr": "height",
                    "value": "32",
                    "class": "0",
                },
                {
                    "field": "MIN(% Customers of Selected States)",
                    "attr": "title",
                    "scope": "cols",
                    "value": "",
                    "class": "0",
                },
                {
                    "field": "MIN(One)",
                    "attr": "display",
                    "scope": "cols",
                    "value": "false",
                },
            ],
        },
    )
    editor.set_worksheet_rich_title(
        "Customers", [{"text": "<Customers Heading>", "fontsize": 10}]
    )
    editor.add_worksheet("State List")
    editor.configure_layered_chart(
        "State List",
        columns=["MIN(One)"],
        rows=["State"],
        axis_shelf="columns",
        hide_axes=True,
        panes=[
            {
                "axis": "MIN(One)",
                "mark_type": "Bar",
                "label": "State Label",
                "label_runs": [
                    {
                        "field": "State Label",
                        "fontcolor": "#ffffff",
                        "fontsize": "8",
                        "fontalignment": "0",
                    }
                ],
                "mark_sizing_off": True,
                "detail": "State",
                "selection_relaxation": "disallow",
            }
        ],
        filters=[{"column": "Show Selected State", "values": [True]}],
    )
    editor.configure_worksheet_style(
        "State List",
        hide_axes=True,
        hide_row_field_labels=True,
        hide_row_label="State",
        hide_gridlines=True,
        hide_borders=True,
        disable_tooltip=False,
        background_color="#f5f5f5",
        hide_table_dividers=True,
        hide_sort_controls=True,
        pane_mark_style={
            "mark-color": "#7c00b2",
            "size": "1.989",
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
        },
        pane_datalabel_style={"color": "#ffffff"},
        axis_style={
            "encodings": [
                {
                    "field": "MIN(One)",
                    "attr": "space",
                    "type": "space",
                    "scope": "cols",
                    "field-type": "quantitative",
                    "min": "0",
                    "max": "1",
                    "range-type": "fixed",
                }
            ]
        },
        pane_cell_style={
            "font-size": "8",
            "font-color": "#ffffff",
            "text-align": "left",
        },
        cell_formats=[{"field": "State", "height": "28"}],
    )
    editor.configure_custom_tooltip("State List", [{"text": "CLICK TO REMOVE"}])

    def zone(kind, x, y, width, height, **options):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1000 * 100000),
                "y": round(y / 800 * 100000),
                "w": round(width / 1000 * 100000),
                "h": round(height / 800 * 100000),
            },
            **options,
        }

    editor.add_dashboard(
        DASHBOARD,
        width=1000,
        height=800,
        worksheet_names=["Map", "State List", "Sales", "Orders", "Customers"],
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    8,
                    984,
                    41,
                    text="How much do these states contribute to the total?",
                    font_size=16,
                    font_color="#7c00b2",
                    bold=True,
                ),
                zone(
                    "worksheet",
                    8,
                    49,
                    328,
                    119,
                    name="Sales",
                    fit="width",
                    style={"margin": "4"},
                ),
                zone(
                    "worksheet",
                    336,
                    49,
                    328,
                    119,
                    name="Orders",
                    fit="width",
                    style={"margin": "4"},
                ),
                zone(
                    "worksheet",
                    664,
                    49,
                    328,
                    119,
                    name="Customers",
                    fit="width",
                    style={"margin": "4"},
                ),
                zone(
                    "text",
                    8,
                    168,
                    984,
                    43,
                    text="Click state(s) in map to add it to the proportional set",
                    font_size=12,
                    style={"background-color": "#f5f5f5"},
                    runs=[
                        {
                            "text": "Click state(s) in map to add it to the proportional set",
                            "font_size": "12",
                            "font_color": "#777777",
                            "font_alignment": "0",
                        }
                    ],
                ),
                zone(
                    "worksheet",
                    8,
                    211,
                    807,
                    517,
                    name="Map",
                    show_title=False,
                    fit="entire",
                    style={"margin": "4"},
                ),
                zone(
                    "container",
                    815,
                    221,
                    177,
                    497,
                    direction="vertical",
                    style={
                        "background-color": "#f5f5f5",
                        "margin": "10",
                        "padding": "10",
                    },
                    children=[
                        {
                            "type": "text",
                            "text": "Click state(s) to\nremove from set",
                            "font_size": "10",
                            "font_color": "#555555",
                            "fixed_size": 54,
                        },
                        {
                            "type": "worksheet",
                            "name": "State List",
                            "show_title": False,
                            "fit": "width",
                        },
                    ],
                ),
                zone(
                    "text",
                    8,
                    728,
                    328,
                    32,
                    text="DESIGNED BY : SEAN MILLER",
                    font_color="#7c00b2",
                    font_size=8,
                ),
                zone(
                    "text",
                    336,
                    728,
                    328,
                    32,
                    text="#WOW2020 | WEEK 20",
                    font_color="#7c00b2",
                    font_size=8,
                ),
                zone(
                    "text",
                    664,
                    728,
                    328,
                    32,
                    text="RECREATED WITH CWTWB",
                    font_color="#7c00b2",
                    font_size=8,
                ),
                zone(
                    "text",
                    8,
                    760,
                    984,
                    32,
                    text="https://www.workout-wednesday.com/2020w20/",
                    font_color="#006080",
                    font_size=8,
                ),
            ],
        },
    )
    editor.add_dashboard_set_action(
        DASHBOARD,
        "Map",
        "Selected States",
        event_type="on-select",
        caption="Add to Set",
        clear_option="do-nothing",
        selection_mode="add",
    )
    editor.add_dashboard_set_action(
        DASHBOARD,
        "State List",
        "Selected States",
        event_type="on-select",
        caption="Remove From Set",
        clear_option="do-nothing",
        selection_mode="remove",
    )
    editor.add_dashboard_action(
        DASHBOARD,
        "filter",
        source_sheet="Map",
        target_sheet="Map",
        field_mappings={"True": "False"},
        caption="Auto Deselect",
        clear_behavior="show-all",
    )
    editor.set_active_dashboard(DASHBOARD)
    path = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    path.parent.mkdir(parents=True, exist_ok=True)
    editor.save(path, validate=False)
    return path


if __name__ == "__main__":
    print(build())
