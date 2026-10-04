"""Build a signed country histogram using extracted data and public SDK only."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_12_16_WW51_Divergent_Histogram"
INPUT = "2020_12_16_WW51_World Indicators_Migrated Data.hyper"
COLORS = {"Life Expectancy Female": "#a39fc9", "Life Expectancy Male": "#31a1b3"}


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(HERE / "inputs" / INPUT))
    e.add_calculated_field(
        "Life Expectancy Age",
        "[Pivot Field Values]",
        datatype="integer",
        role="dimension",
        field_type="quantitative",
    )
    e.add_calculated_field(
        "Country Count",
        "IF CONTAINS(ATTR([Pivot Field Names]),'Female') THEN COUNTD([Country/Region]) ELSE -COUNTD([Country/Region]) END",
        datatype="integer",
    )
    e.set_field_format("Country Count", "n#,##0;#,##0")
    e.add_calculated_field(
        "Max Count Ref Line",
        "WINDOW_MAX([Country Count])",
        datatype="integer",
        table_calc="Rows",
    )
    e.add_calculated_field(
        "Max Count Ref Line (copy)",
        "-WINDOW_MAX([Country Count])",
        datatype="integer",
        table_calc="Rows",
    )
    e.add_calculated_field(
        "Year Label",
        "STR(YEAR(MIN([Year])))",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Has Life Expectancy",
        "NOT ISNULL([Pivot Field Values])",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    filters = [
        {"column": "YEAR(Year)", "values": [2012]},
        {"column": "Has Life Expectancy", "values": [True]},
    ]
    e.add_worksheet("Viz")
    e.configure_layered_chart(
        "Viz",
        columns=["[Life Expectancy Age]"],
        rows=["Country Count"],
        panes=[
            {
                "axis": "Country Count",
                "mark_type": "Bar",
                "breakdown": "off",
                "color": "Pivot Field Names",
                "color_map": COLORS,
                "detail_extra": ["Max Count Ref Line", "Max Count Ref Line (copy)"],
                "labels": ["Country Count"],
                "tooltip": [
                    "ATTR(Year)",
                    "[Life Expectancy Age]",
                    "Pivot Field Names",
                    "Country Count",
                ],
                "mark_sizing": {
                    "custom-mark-size-in-axis-units": 1.0,
                    "mark-alignment": "mark-alignment-left",
                    "mark-sizing-setting": "marks-scaling-on",
                    "use-custom-mark-size": False,
                },
                "mark_style": {
                    "size": "1.8790607452392578",
                    "has-stroke": "true",
                    "stroke-color": "#ffffff",
                    "mark-labels-cull": "false",
                    "mark-labels-mode": "range",
                    "mark-labels-range-scope": "pane",
                    "mark-labels-show": "true",
                },
                "datalabel_style": {"color-mode": "match", "font-weight": "bold"},
            }
        ],
        filters=filters,
        table_calc_overrides={
            name: [
                {
                    "ordering_type": "Field",
                    "order": [
                        {"field": "[Life Expectancy Age]", "reference": "instance"},
                        "Pivot Field Names",
                    ],
                }
            ]
            for name in ["Max Count Ref Line", "Max Count Ref Line (copy)"]
        },
    )
    for index, (field, formula) in enumerate(
        [("Max Count Ref Line", "min"), ("Max Count Ref Line (copy)", "max")]
    ):
        e.add_reference_line(
            "Viz",
            axis_field="Country Count",
            value_field=field,
            formula=formula,
            label_type="none",
            tooltip="",
            probability=None,
        )
        e.configure_reference_line_style(
            "Viz",
            f"refline{index}",
            {
                "line-visibility": "off",
                "stroke-size": 0,
                "fill-above": "#00000000",
                "fill-below": "#00000000",
            },
        )
    e.add_calculated_field("Zero Axis Line", "0", datatype="integer")
    e.add_reference_line(
        "Viz",
        axis_field="Country Count",
        value_field="MIN(Zero Axis Line)",
        formula="min",
        label_type="none",
        tooltip="",
        probability=None,
    )
    e.configure_reference_line_style(
        "Viz",
        "refline2",
        {
            "line-visibility": "on",
            "line-pattern-only": "solid",
            "stroke-size": 2,
            "stroke-color": "#c0c0c0",
        },
    )
    e.configure_custom_tooltip(
        "Viz",
        [
            {"field": "ATTR(Year)", "bold": True, "fontsize": 12},
            {"text": " | ", "bold": True, "fontcolor": "#898989", "fontsize": 12},
            {"field": "Pivot Field Names", "bold": True, "fontsize": 12},
            {"text": " ", "fontsize": 12},
            {"field": "[Life Expectancy Age]", "bold": True, "fontsize": 12},
            {"text": " years\n# Countries: ", "bold": True, "fontcolor": "#898989"},
            {"field": "Country Count", "bold": True},
        ],
    )
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_borders=True,
        hide_zeroline=True,
        pane_datalabel_style={"color-mode": "match", "font-weight": "bold"},
        table_dividers=[
            {
                "scope": "rows",
                "stroke-size": 3,
                "stroke-color": "#c0c0c0",
                "line-visibility": "on",
            }
        ],
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_sort_controls=True,
        axis_style={
            "per_field": [
                {
                    "field": "[Life Expectancy Age]",
                    "scope": "cols",
                    "attr": "title",
                    "value": "AVG. LIFE EXPECTANCY",
                    "class": 0,
                },
                {
                    "field": "Country Count",
                    "scope": "rows",
                    "attr": "display",
                    "value": "false",
                    "class": 0,
                },
            ],
            "encodings": [
                {
                    "field": "[Life Expectancy Age]",
                    "attr": "space",
                    "class": 0,
                    "scope": "cols",
                    "type": "space",
                    "range-type": "fixed",
                    "min": 30,
                    "max": 95,
                }
            ],
        },
        cell_formats=[{"field": "ATTR(Year)", "text-format": "*yyyy"}],
    )
    e.set_worksheet_title("Viz", "")
    e.add_worksheet("Title")
    e.configure_chart("Title", mark_type="Text", label="Year Label", filters=filters)
    e.configure_custom_label(
        "Title",
        [
            {
                "text": "GLOBAL DISTRIBUTION OF AVERAGE LIFE EXPECTANCY BY SEX ",
                "bold": True,
                "fontsize": 14,
            },
            {"text": "(", "fontsize": 10, "bold": True},
            {"field": "Year Label", "fontsize": 10, "bold": True},
            {"text": ")\n", "fontsize": 10, "bold": True},
            {"text": "FEMALE", "fontcolor": "#a39fc9", "fontsize": 10, "bold": True},
            {"text": "  VS.  ", "fontsize": 10, "bold": True},
            {"text": "MALE", "fontcolor": "#31a1b3", "fontsize": 10, "bold": True},
        ],
    )
    e.configure_worksheet_style(
        "Title",
        hide_axes=True,
        hide_borders=True,
        hide_gridlines=True,
        hide_zeroline=True,
        disable_tooltip=True,
        pane_cell_style={"text-align": "left", "vertical-align": "center"},
    )
    e.set_worksheet_title("Title", "")
    e.link_worksheet_filters("YEAR(Year)", ["Viz", "Title"])
    e.add_dashboard(
        DASHBOARD,
        width=1300,
        height=800,
        layout={
            "type": "container",
            "direction": "vertical",
            "style": {"margin": 8},
            "children": [
                {
                    "type": "container",
                    "direction": "horizontal",
                    "fixed_size": 68,
                    "children": [
                        {
                            "type": "worksheet",
                            "name": "Title",
                            "show_title": False,
                            "fit": "entire",
                        },
                        {
                            "type": "container",
                            "direction": "vertical",
                            "fixed_size": 160,
                            "children": [
                                {
                                    "type": "text",
                                    "runs": [
                                        {
                                            "text": "YEAR",
                                            "font_size": 10,
                                            "font_alignment": "0",
                                        }
                                    ],
                                    "fixed_size": 22,
                                },
                                {
                                    "type": "filter",
                                    "worksheet": "Viz",
                                    "field": "YEAR(Year)",
                                    "mode": "dropdown",
                                    "show_all": False,
                                    "show_title": False,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "worksheet",
                    "name": "Viz",
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
                                    "text": "DESIGNED BY : ANN JACKSON",
                                    "font_size": 8,
                                    "font_color": "#31a1b3",
                                    "font_alignment": "0",
                                    "bold": True,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "#WOW2020 | WEEK 51",
                                    "font_size": 8,
                                    "font_color": "#31a1b3",
                                    "font_alignment": "1",
                                    "bold": True,
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "runs": [
                                {
                                    "text": "RECREATED WITH CWTWB",
                                    "font_size": 8,
                                    "font_color": "#31a1b3",
                                    "font_alignment": "2",
                                    "bold": True,
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "text",
                    "runs": [
                        {
                            "text": "https://www.workout-wednesday.com/2020w51/",
                            "font_size": 8,
                            "font_color": "#31a1b3",
                            "hyperlink": "https://www.workout-wednesday.com/2020w51/",
                        }
                    ],
                    "fixed_size": 32,
                },
            ],
        },
    )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
