"""Build dynamic category reference lines and three ranking blocks."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_10_07_WW41_RefLine by DImension"
MEASURES = ["Sales Per Order", "Profit Ratio", "Items Per Order"]
COLORS = {"Technology": "#00a2b3", "Furniture": "#8fb202", "Office Supplies": "#cf3e53"}


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    e.add_parameter(
        "SELECT A MEASURE",
        datatype="string",
        default_value="Sales Per Order",
        internal_name="[ParameterMeasure]",
        domain_type="list",
        allowed_values=MEASURES,
    )
    formulas = {
        "Profit Ratio": "SUM([Profit])/SUM([Sales])",
        "Sales Per Order": "SUM([Sales])/COUNTD([Order ID])",
        "Items Per Order": "SUM([Quantity])/COUNTD([Order ID])",
        "Display Measure": "CASE [SELECT A MEASURE] WHEN 'Profit Ratio' THEN ROUND([Profit Ratio]*100,1) WHEN 'Sales Per Order' THEN ROUND([Sales Per Order],0) ELSE ROUND([Items Per Order],2) END",
        "Ref Line per Category": "WINDOW_AVG([Display Measure])",
        "Rank": "RANK([Ref Line per Category])",
        "Display Ref Line": "CASE [SELECT A MEASURE] WHEN 'Profit Ratio' THEN STR(ROUND([Ref Line per Category],1)) WHEN 'Sales Per Order' THEN STR(ROUND([Ref Line per Category],0)) ELSE STR(ROUND([Ref Line per Category],2)) END",
    }
    for name, formula in formulas.items():
        e.add_calculated_field(
            name,
            formula,
            datatype="string" if name == "Display Ref Line" else "real",
            field_type="nominal" if name == "Display Ref Line" else "quantitative",
            table_calc="Columns"
            if name in {"Ref Line per Category", "Rank", "Display Ref Line"}
            else None,
            default_format="N"
            if name in {"Display Measure", "Ref Line per Category"}
            else "",
        )
    for name, formula in {
        "$ Label Prefix": "IF [SELECT A MEASURE]='Sales Per Order' THEN '$' ELSE '' END",
        "% Label Suffix": "IF [SELECT A MEASURE]='Profit Ratio' THEN '%' ELSE '' END",
        "Label:Category": "UPPER([Category])",
    }.items():
        e.add_calculated_field(
            name, formula, datatype="string", role="dimension", field_type="nominal"
        )
    for category in COLORS:
        e.add_calculated_field(
            f"Ref Line - {category}",
            f"IF MIN([Category])='{category}' THEN [Ref Line per Category] END",
            table_calc="Columns",
        )
    e.set_datasource_color_palette("Category", COLORS)
    e.add_worksheet("Line")
    e.add_calculated_field(
        "Metric Label",
        "[SELECT A MEASURE]",
        datatype="string",
        role="dimension",
        field_type="nominal",
    )
    e.add_calculated_field(
        "Quarter Date",
        "DATE(DATETRUNC('quarter',[Order Date]))",
        datatype="date",
        role="dimension",
        field_type="quantitative",
    )
    quarter = "QUARTERTRUNC(Order Date)"
    address = {
        "ordering_type": "Field",
        "order": [quarter, "$ Label Prefix", "% Label Suffix"],
    }
    overrides = {
        "Ref Line per Category": [address],
        "Display Ref Line": [
            {"ordering_type": "Rows"},
            {"field": "Ref Line per Category", **address},
        ],
        **{
            f"Ref Line - {c}": [
                {"ordering_type": "Rows"},
                {"field": "Ref Line per Category", **address},
            ]
            for c in COLORS
        },
    }
    e.configure_layered_chart(
        "Line",
        columns=[quarter],
        rows=["Metric Label", "Display Measure", "Ref Line per Category"],
        panes=[
            {
                "axis": "Display Measure",
                "mark_type": "Line",
                "color": "Category",
                "detail_extra": [f"Ref Line - {c}" for c in COLORS],
                "labels": ["Display Measure", "$ Label Prefix", "% Label Suffix"],
                "label_runs": [
                    {"field": "$ Label Prefix"},
                    {"field": "Display Measure"},
                    {"field": "% Label Suffix"},
                ],
                "mark_style": {
                    "size": "0.6",
                    "mark-labels-show": "true",
                    "mark-labels-mode": "range",
                    "mark-labels-range-scope": "multi-mark",
                    "mark-labels-cull": "false",
                    "mark-labels-range-field": "Display Measure",
                },
            },
            {
                "axis": "Ref Line per Category",
                "mark_type": "Line",
                "color": "Category",
                "labels": [
                    "Label:Category",
                    "Display Ref Line",
                    "$ Label Prefix",
                    "% Label Suffix",
                ],
                "label_runs": [
                    {"field": "Label:Category"},
                    {"text": ": "},
                    {"field": "$ Label Prefix"},
                    {"field": "Display Ref Line"},
                    {"field": "% Label Suffix"},
                ],
                "mark_style": {
                    "mark-transparency": "0",
                    "mark-labels-show": "true",
                    "mark-labels-mode": "line-ends",
                    "mark-labels-line-first": "true",
                    "mark-labels-line-last": "false",
                },
            },
        ],
        synchronized=True,
        fold_axes=True,
        table_calc_overrides=overrides,
    )
    for index, (category, color) in enumerate(COLORS.items()):
        e.add_reference_line(
            "Line",
            axis_field="Display Measure",
            value_field=f"Ref Line - {category}",
            label_type="none",
            tooltip="",
            pane_index=0,
        )
        e.configure_reference_line_style(
            "Line",
            f"refline{index}",
            {"line-pattern-only": "dotted", "stroke-color": color, "stroke-size": 1},
        )
    e.configure_worksheet_style(
        "Line",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        axis_style={
            "per_field": [
                {
                    "field": "Ref Line per Category",
                    "scope": "rows",
                    "class": 0,
                    "attr": "display",
                    "value": "false",
                },
                {
                    "field": "Display Measure",
                    "scope": "rows",
                    "class": 0,
                    "attr": "title",
                    "value": "",
                },
                {
                    "field": quarter,
                    "scope": "cols",
                    "class": 0,
                    "attr": "title",
                    "value": "",
                },
            ]
        },
        pane_datalabel_style={
            "color-mode": "match",
            "font-size": 8,
            "font-weight": "bold",
        },
    )
    e.configure_worksheet_style(
        "Line",
        label_formats=[
            {
                "field": "Metric Label",
                "text-orientation": "-90",
                "font-weight": "bold",
                "font-size": "9",
            }
        ],
        hide_table_dividers=True,
    )
    e.set_worksheet_title("Line", "")
    e.configure_worksheet_style(
        "Line",
        panes_style={
            "1": {
                "datalabel": {
                    "color-mode": "match",
                    "font-size": 8,
                    "font-weight": "bold",
                }
            },
            "2": {
                "datalabel": {
                    "color-mode": "match",
                    "font-size": 8,
                    "font-weight": "bold",
                },
                "cell": {"vertical-align": "top"},
            },
        },
    )
    for field in ("Block Axis", "Text Axis"):
        e.add_calculated_field(field, "MIN(0.5)")
    for rank in range(1, 4):
        sheet = f"Rank{rank}"
        e.add_worksheet(sheet)
        address = {
            "ordering_type": "Field",
            "order": ["$ Label Prefix", "% Label Suffix"],
        }
        e.configure_layered_chart(
            sheet,
            panes=[
                {
                    "mark_type": "Automatic",
                    "color": "Category",
                    "size": "Ref Line per Category",
                    "labels": [
                        "Display Ref Line",
                        "Category",
                        "$ Label Prefix",
                        "% Label Suffix",
                    ],
                    "label_runs": [
                        {
                            "field": "$ Label Prefix",
                            "fontsize": 24 if rank == 1 else 16,
                            "fontcolor": "#ffffff",
                            "bold": True,
                        },
                        {
                            "field": "Display Ref Line",
                            "fontsize": 24 if rank == 1 else 16,
                            "fontcolor": "#ffffff",
                            "bold": True,
                        },
                        {
                            "field": "% Label Suffix",
                            "fontsize": 24 if rank == 1 else 16,
                            "fontcolor": "#ffffff",
                            "bold": True,
                        },
                        {"text": "\n"},
                        {
                            "field": "Category",
                            "fontsize": 18 if rank == 1 else 12,
                            "fontcolor": "#ffffff",
                            "bold": True,
                        },
                    ],
                    "mark_style": {
                        "mark-labels-show": "true",
                        "mark-labels-cull": "false",
                    },
                }
            ],
            filters=[
                {
                    "column": "Rank",
                    "type": "quantitative",
                    "min": str(rank),
                    "max": str(rank),
                }
            ],
            table_calc_overrides={
                "Ref Line per Category": [address],
                "Rank": [
                    {"ordering_type": "Field", "ordering_field": "Category"},
                    {"field": "Ref Line per Category", **address},
                ],
                "Display Ref Line": [
                    {"ordering_type": "Rows"},
                    {"field": "Ref Line per Category", **address},
                ],
            },
            table_calc_context=True,
        )
        e.configure_worksheet_style(
            sheet,
            hide_axes=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_borders=True,
            hide_table_dividers=True,
            pane_cell_style={"text-align": "center", "vertical-align": "center"},
        )

    def zone(kind, x, y, w, h, **kwargs):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 1100 * 100000),
                "y": round(y / 550 * 100000),
                "w": round(w / 1100 * 100000),
                "h": round(h / 550 * 100000),
            },
            "style": {"margin": 4},
            **kwargs,
        }

    zones = [
        zone(
            "text",
            8,
            8,
            799,
            56,
            runs=[
                {
                    "text": "Quarterly ",
                    "font_size": 14,
                    "bold": True,
                    "font_alignment": "0",
                },
                {
                    "parameter": "SELECT A MEASURE",
                    "font_size": 14,
                    "bold": True,
                    "font_alignment": "0",
                },
                {
                    "text": " Performance by Category",
                    "font_size": 14,
                    "bold": True,
                    "font_alignment": "0",
                },
            ],
        ),
        zone("worksheet", 8, 64, 799, 446, name="Line", fit="entire", show_title=False),
        zone(
            "paramctrl", 807, 8, 285, 56, parameter="SELECT A MEASURE", mode="dropdown"
        ),
        zone(
            "worksheet", 807, 64, 285, 303, name="Rank1", fit="entire", show_title=False
        ),
        zone(
            "worksheet",
            807,
            367,
            142.5,
            143,
            name="Rank2",
            fit="entire",
            show_title=False,
        ),
        zone(
            "worksheet",
            949.5,
            367,
            142.5,
            143,
            name="Rank3",
            fit="entire",
            show_title=False,
        ),
    ]
    for text, x, w in [
        ("DESIGNED BY : ANN JACKSON", 8, 209),
        ("#WOW2020 | WEEK 41 | www.workout-wednesday.com/2020w41/", 217, 590),
        ("Recreated by @DonnaColes30", 807, 285),
    ]:
        zones.append(
            zone(
                "text",
                x,
                510,
                w,
                32,
                runs=[
                    {
                        "text": text,
                        "font_size": 8,
                        "font_color": "#cf3e53",
                        "font_alignment": "0",
                    }
                ],
            )
        )
    e.add_dashboard(
        DASHBOARD,
        width=1100,
        height=550,
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": zones,
        },
    )
    output = (
        Path(output_path) if output_path else HERE / "outputs/replicated-workbook.twbx"
    )
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
