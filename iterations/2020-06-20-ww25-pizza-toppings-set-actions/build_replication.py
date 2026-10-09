"""Build the five-sheet pizza menu from locked Hyper data and PNG assets."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_06_17_WW25_PizzaToppings_Set_Actions"
SELECTED = [
    "Classic",
    "Ground Beef",
    "Jalapeno Peppers",
    'Large 13.5"',
    "No Sauce",
    "Pineapple",
    "Pork Meatballs",
    "Red Peppers",
]
TYPE_COLORS = {
    "Toppings": "#5b198f",
    "Crust": "#de8529",
    "Sauce": "#fd6666",
    "Size": "#edc948",
}


def build():
    e = TWBEditor("")
    e.set_hyper_connection(
        str(HERE / "inputs/Sheet1 (2020_06_17_WW25_Pizza Toppings).hyper")
    )
    e.add_parameter(
        "Budget",
        datatype="integer",
        default_value="15",
        domain_type="any",
        default_format='c"£"#,##0',
    )
    e.add_set("Selected Products", "Product", members=SELECTED)
    specs = [
        (
            "Selected Product Indicator",
            "IF [Selected Products] THEN '✔' ELSE '' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Veg Indicator",
            "IF [Vegetarian]='Yes' THEN '●' ELSE '' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Selection Color",
            "[Type] + IF [Selected Products] THEN '|selected' ELSE '|available' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Product Copy",
            "[Product]",
            "string",
            "dimension",
            "nominal",
        ),
        ("One", "1.0", "real", "measure", "quantitative"),
        (
            "Stack Order",
            "CASE [Type] WHEN 'Size' THEN 1 WHEN 'Crust' THEN 2 WHEN 'Sauce' THEN 3 ELSE 4 END",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Type Order",
            "CASE [Type] WHEN 'Size' THEN 4 WHEN 'Crust' THEN 3 WHEN 'Sauce' THEN 2 ELSE 1 END",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Selected Total",
            "{FIXED:SUM(IF [Selected Products] THEN [Price] ELSE 0 END)}",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Selected Price",
            "IF [Selected Products] THEN [Price] END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Budget Value",
            "[Parameters].[Parameter 1]",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Budget Difference",
            "MIN([Budget Value])-MIN([Selected Total])",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Under Budget",
            "IF [Budget Difference]>=0 THEN [Budget Difference] END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Over Budget",
            "IF [Budget Difference]<0 THEN ABS([Budget Difference]) END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "Over Budget Text",
            "IF [Budget Difference]<0 THEN ' Over Budget' ELSE '' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Under Budget Text",
            "IF [Budget Difference]>=0 THEN ' Under Budget' ELSE '' END",
            "string",
            "dimension",
            "nominal",
        ),
        ("True", "TRUE", "boolean", "dimension", "nominal"),
        ("False", "FALSE", "boolean", "dimension", "nominal"),
        ("Zero", "0.0", "real", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, kind in specs:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=kind
        )
    for field in [
        "Price",
        "Selected Price",
        "Selected Total",
        "Budget Value",
        "Budget Difference",
        "Under Budget",
        "Over Budget",
    ]:
        e.set_field_format(field, 'c"£"#,##0.00;-"£"#,##0.00')
    e.set_field_format("Budget Value", 'c"\u00a3"#,##0;-"\u00a3"#,##0')
    e.set_datasource_color_palette("Type", TYPE_COLORS)
    selected_colors = {
        "Toppings": "#00154d",
        "Crust": "#a66022",
        "Sauce": "#b00003",
        "Size": "#c18e09",
    }
    e.set_datasource_color_palette(
        "Selection Color",
        {
            f"{kind}|{status}": (
                selected_colors[kind] if status == "selected" else color
            )
            for kind, color in TYPE_COLORS.items()
            for status in ("selected", "available")
        },
    )
    e.set_shape_palette(
        "Type",
        {
            kind: str(HERE / "inputs/shapes" / f"{kind}-150x150.png")
            for kind in TYPE_COLORS
        },
        palette="Custom",
    )
    for sheet in [
        "Chart",
        "List of Items",
        "Selector",
        "Total Bar",
        "Under Over Budget",
    ]:
        e.add_worksheet(sheet)
    e.configure_chart(
        "Chart",
        mark_type="Bar",
        rows=[
            "Type",
            "Product Copy",
            "Selected Product Indicator",
            "Product",
            "Veg Indicator",
        ],
        columns=["SUM(Price)"],
        color="Selection Color",
        label="SUM(Price)",
        tooltip=["Product", "SUM(Price)", "Vegetarian"],
        sort_descending="MIN(Type Order)",
        sort_field="Type",
    )
    e.configure_chart(
        "List of Items",
        mark_type="Automatic",
        rows=["Type", "Product"],
        columns=["MIN(One)"],
        color="Type",
        label="Product",
        label_runs=[{"field": "Product", "fontcolor": "#ffffff", "fontsize": "8"}],
        filters=[{"column": "Selected Products", "values": [True]}],
        sort_descending="MIN(Type Order)",
        sort_field="Type",
        tooltip=["SUM(Price)", "Product"],
        axis_fixed_range={"column": "MIN(One)", "min": 0, "max": 1},
    )
    e.configure_layered_chart(
        "Selector",
        rows=["Type"],
        panes=[
            {
                "mark_type": "Shape",
                "shape": "Type",
                "mark_sizing_off": True,
            }
        ],
        sort_descending="MIN(Type Order)",
        sort_field="Type",
        hide_axes=True,
    )
    e.configure_layered_chart(
        "Total Bar",
        columns=["SUM(Selected Price)", "MIN(Selected Total)"],
        panes=[
            {
                "axis": "SUM(Selected Price)",
                "mark_type": "Bar",
                "color": "Type",
                "mark_style": {"size": "0.6037", "mark-labels-show": "false"},
                "tooltip": ["SUM(Selected Price)", "Type"],
            },
            {
                "axis": "MIN(Selected Total)",
                "mark_type": "Text",
                "labels": ["MIN(Selected Total)"],
                "mark_style": {
                    "mark-labels-show": "true",
                    "font-size": "10",
                },
            },
        ],
        sort_descending="MIN(Stack Order)",
        sort_field="Type",
        axis_shelf="cols",
        fold_axes=True,
        hide_axes=True,
    )
    e.add_reference_line(
        "Total Bar",
        axis_field="SUM(Selected Price)",
        value_field="MIN(Budget Value)",
        scope="per-table",
        label_type="custom",
        label="Pizza Budget : <Value>",
        tooltip="Budget = <Value>",
    )
    e.configure_chart(
        "Under Over Budget",
        mark_type="Text",
        label_runs=[
            {"field": "Over Budget", "fontcolor": "#d81159", "fontsize": "9"},
            {"field": "Over Budget Text", "fontcolor": "#d81159", "fontsize": "9"},
            {"field": "Under Budget", "fontcolor": "#008682", "fontsize": "9"},
            {"field": "Under Budget Text", "fontcolor": "#008682", "fontsize": "9"},
        ],
        label_extra=[
            "Over Budget",
            "Under Budget",
            "Over Budget Text",
            "Under Budget Text",
        ],
        tooltip=["MIN(Selected Total)", "Budget Difference"],
    )
    for sheet in [
        "Chart",
        "List of Items",
        "Selector",
        "Total Bar",
        "Under Over Budget",
    ]:
        e.set_worksheet_title(sheet, "")
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            hide_row_field_labels=True,
            hide_col_field_labels=True,
            hide_sort_controls=True,
        )
    e.configure_worksheet_style(
        "Chart",
        hide_row_label="Type",
        panes_style={
            "1": {
                "mark_style": {
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                }
            }
        },
    )
    e.configure_worksheet_style(
        "Selector",
        hide_row_label="Type",
        panes_style={
            "1": {
                "mark_style": {
                    "size": "2.0",
                    "mark-labels-show": "true",
                    "mark-labels-cull": "false",
                }
            }
        },
    )

    e.set_worksheet_rich_title(
        "Total Bar",
        [
            {
                "text": "Price vs Budget",
                "fontsize": 12,
                "fontcolor": "#333333",
                "fontalignment": "0",
            }
        ],
    )
    e.configure_reference_line_style(
        "Total Bar",
        "refline0",
        {
            "vertical-align": "top",
            "text-align": "right",
            "color": "#000000",
            "stroke-color": "#b0b0b0",
            "stroke-size": "4",
            "font-size": "11",
            "font-weight": "bold",
            "line-visibility": "on",
        },
    )
    e.configure_worksheet_style(
        "Chart",
        label_formats=[
            {"field": "Type", "display": False},
            {"field": "Product Copy", "display": False},
            {"field": "Veg Indicator", "color": "#008682"},
        ],
        pane_mark_style={
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
            "font-size": "8",
        },
    )
    e.configure_worksheet_style(
        "List of Items",
        label_formats=[
            {"field": "Type", "display": False},
            {"field": "Product", "display": False},
        ],
        pane_mark_style={
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
            "font-size": "8",
            "color-mode": "user",
            "color": "#ffffff",
        },
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        hide_band_color=True,
    )
    e.configure_worksheet_style(
        "Selector", pane_mark_style={"size": "1.857", "mark-labels-show": "false"}
    )
    e.configure_worksheet_style(
        "Under Over Budget",
        pane_mark_style={
            "mark-labels-show": "true",
            "mark-labels-cull": "false",
            "font-size": "10",
        },
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
    )

    e.configure_worksheet_style(
        "Chart",
        header_formats=[
            {"field": "Selected Product Indicator", "width": "28"},
            {"field": "Veg Indicator", "width": "28"},
        ],
        label_formats=[
            {"field": "Product", "font-size": "8"},
            {"field": "Veg Indicator", "color": "#59a14f"},
        ],
    )

    e.configure_worksheet_style(
        "List of Items",
        pane_datalabel_style={
            "color-mode": "user",
            "color": "#ffffff",
            "font-size": "8",
        },
    )
    e.configure_worksheet_style(
        "Total Bar", panes_style={"2": {"cell_style": {"text-align": "right"}}}
    )

    def zone(kind, x, y, w, h, **options):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 800 * 100000),
                "y": round(y / 500 * 100000),
                "w": round(w / 800 * 100000),
                "h": round(h / 500 * 100000),
            },
            **options,
        }

    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=500,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    17,
                    784,
                    35,
                    text="PIZZAToppings",
                    font_size=18,
                    font_color="#000000",
                ),
                zone(
                    "worksheet",
                    8,
                    53,
                    650,
                    125,
                    name="Total Bar",
                    fit="entire",
                    show_title=True,
                ),
                zone(
                    "paramctrl",
                    200,
                    67,
                    144,
                    30,
                    parameter="Budget",
                    control_caption="Set Budget",
                    show_title=True,
                    mode="type_in",
                ),
                zone(
                    "worksheet",
                    388,
                    68,
                    266,
                    25,
                    name="Under Over Budget",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "worksheet",
                    8,
                    178,
                    101,
                    250,
                    name="Selector",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "worksheet",
                    109,
                    178,
                    549,
                    250,
                    name="Chart",
                    fit="entire",
                    show_title=False,
                ),
                zone("text", 658, 80, 134, 40, text="List of Items", font_size=12),
                zone(
                    "worksheet",
                    658,
                    120,
                    134,
                    308,
                    name="List of Items",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "text",
                    8,
                    428,
                    261,
                    32,
                    runs=[
                        {
                            "text": "DESIGNED BY : LORNA BROWN",
                            "font_size": "8",
                            "font_color": "#5b198f",
                            "font_alignment": "0",
                        }
                    ],
                ),
                zone(
                    "text",
                    269,
                    428,
                    262,
                    32,
                    runs=[
                        {
                            "text": "#WOW2020 | WEEK 25",
                            "font_size": "8",
                            "font_color": "#5b198f",
                            "font_alignment": "1",
                        }
                    ],
                ),
                zone(
                    "text",
                    531,
                    428,
                    261,
                    32,
                    runs=[
                        {
                            "text": "RECREATED WITH CWTWB",
                            "font_size": "8",
                            "font_color": "#5b198f",
                            "font_alignment": "2",
                        }
                    ],
                ),
                zone(
                    "text",
                    8,
                    460,
                    784,
                    32,
                    text="https://www.workout-wednesday.com/2020w25/",
                    font_size=8,
                ),
            ],
        },
    )
    e.add_dashboard_action(
        DASHBOARD,
        "filter",
        source_sheet="Selector",
        target_sheet="Chart",
        fields=["Type"],
        caption="Filter Chart",
        clear_behavior="show-all",
    )
    e.initialize_dashboard_filter_action(DASHBOARD, "Filter Chart", {"Type": ["Size"]})
    for sheet in ["Selector", "List of Items"]:
        e.add_dashboard_action(
            DASHBOARD,
            "filter",
            source_sheet=sheet,
            target_sheet=sheet,
            field_mappings={"True": "False"},
            caption=f"{sheet} Deselect",
            clear_behavior="show-all",
        )
    e.add_dashboard_action(
        DASHBOARD,
        "highlight",
        source_sheet="Chart",
        target_sheet="Chart",
        fields=["True"],
        caption="Highlight1",
    )
    for caption, mode in [("Add to Pizza", "add"), ("Remove From Pizza", "remove")]:
        e.add_dashboard_set_action(
            DASHBOARD,
            "Chart",
            "Selected Products",
            event_type="on-menu",
            caption=caption,
            clear_option="do-nothing",
            selection_mode=mode,
        )
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
