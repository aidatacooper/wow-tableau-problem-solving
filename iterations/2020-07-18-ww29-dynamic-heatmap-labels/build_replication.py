"""Build the Intermediate heatmap using locked data and public SDK APIs."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_07_15_WW29_Heatmap_Intermediate"
SHEET = "Chart-Int"
NUMBER_FORMAT = "n#,##0.00;-#,##0.00"


def build(output_path=None):
    editor = TWBEditor("")
    editor.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    calculations = [
        (
            "Month Order Date",
            "DATENAME('month',[Order Date])",
            "string",
            "dimension",
            "nominal",
        ),
        ("Year Order Date", "YEAR([Order Date])", "integer", "dimension", "ordinal"),
        (
            "Month Sort",
            "-DATEPART('month',[Order Date])",
            "integer",
            "measure",
            "quantitative",
        ),
        (
            "Profit Ratio",
            "SUM([Profit])/SUM([Sales])",
            "real",
            "measure",
            "quantitative",
        ),
        ("Size of Years", "SIZE()", "integer", "measure", "quantitative"),
        ("Size of Months", "SIZE()", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, field_type in calculations:
        editor.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=field_type
        )
    editor.add_set("Hover Month Set", "Month Order Date", members=[])
    editor.add_set("Hover Year Set", "Year Order Date", members=[])
    editor.add_calculated_field(
        "Total Label",
        "IF [Size of Years]=1 OR [Size of Months]=1 THEN AVG([Quantity]) END",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    editor.add_calculated_field(
        "Cell Label",
        "IF ATTR([Hover Month Set]) AND ATTR([Hover Year Set]) "
        "AND [Size of Months]>1 AND [Size of Years]>1 THEN AVG([Quantity]) END",
        datatype="real",
        role="measure",
        field_type="quantitative",
    )
    for name in ("Total Label", "Cell Label"):
        editor.set_field_format(name, NUMBER_FORMAT)
    editor.set_field_format("Profit Ratio", "p0%")
    editor.add_worksheet(SHEET)
    contexts = [
        {"ordering_type": "Rows"},
        {
            "field": "Size of Years",
            "ordering_type": "Field",
            "ordering_field": "Year Order Date",
        },
        {
            "field": "Size of Months",
            "ordering_type": "Field",
            "ordering_field": "Month Order Date",
        },
    ]
    editor.configure_layered_chart(
        SHEET,
        columns=["Month Order Date"],
        rows=["Year Order Date"],
        panes=[
            {
                "mark_type": "Square",
                "color": "AVG(Quantity)",
                "label": "Total Label",
                "labels": ["Cell Label"],
                "label_runs": [{"field": "Total Label"}, {"field": "Cell Label"}],
                "tooltip": "Profit Ratio",
                "mark_sizing_off": True,
                "selection_relaxation": "selection-relaxation-disallow",
                "mark_style": {"size": "2.1104972362518311", "has-stroke": "false"},
            }
        ],
        table_calc_overrides={"Total Label": contexts, "Cell Label": contexts},
        sort_field="Month Order Date",
        sort_descending="AVG(Month Sort)",
    )
    editor.configure_subtotals(
        SHEET, measure_fields=["AVG(Quantity)"], aggregation="Average"
    )
    border_formats = [
        {"data_class": kind, "border-width": 5, "border-color": "#ffffff"}
        for kind in ("total", "subtotal")
    ]
    editor.configure_worksheet_style(
        SHEET,
        show_row_totals=True,
        show_column_totals=True,
        hide_axes=True,
        hide_gridlines=True,
        hide_zeroline=True,
        hide_table_dividers=True,
        hide_band_color=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        cell_formats=[{"field": "AVG(Quantity)", "text-format": NUMBER_FORMAT}],
        header_formats=border_formats
        + [{"field": "Year Order Date", "width": 44}]
        + [
            {"field": field, "data_class": "total", "total-label": "Total"}
            for field in ("Year Order Date", "Month Order Date")
        ],
        pane_formats=border_formats,
        label_formats=[
            {"field": field, "font-size": 8}
            for field in ("Year Order Date", "Month Order Date")
        ],
        pane_cell_style={"text-align": "center", "vertical-align": "center"},
        pane_datalabel_style={"color-mode": "auto"},
        legend_style={"font-size": 8},
        color_style={
            "field": "AVG(Quantity)",
            "palette": "green_blue_sequential_10_0",
            "include_totals": True,
        },
    )

    def position(x, y, w, h):
        return {
            "x": round(x / 900 * 100000),
            "y": round(y / 500 * 100000),
            "w": round(w / 900 * 100000),
            "h": round(h / 500 * 100000),
        }

    def text(content, x, y, w, h, *, size=8, color="#000000", bold=False, align="0"):
        return {
            "type": "text",
            "runs": [
                {
                    "text": content,
                    "font_size": size,
                    "font_color": color,
                    "bold": bold,
                    "font_alignment": align,
                }
            ],
            "absolute": position(x, y, w, h),
        }

    zones = [
        text(
            "Can you dynamically display a label on a heatmap?",
            8,
            8,
            884,
            49.36,
            size=11,
            bold=True,
        ),
        {
            "type": "empty",
            "absolute": position(13, 49, 420, 2),
            "style": {"background-color": "#000000"},
        },
        text("Average Quantity Sold", 8, 57.36, 177, 35.26),
        {
            "type": "color",
            "worksheet": SHEET,
            "field": "AVG(Quantity)",
            "show_title": False,
            "pane_index": 1,
            "absolute": position(185, 57.36, 228, 35.26),
        },
        {
            "type": "worksheet",
            "name": SHEET,
            "show_title": False,
            "fit": "entire",
            "absolute": position(8, 92.62, 884, 360.65),
        },
        text(
            "DESIGNED BY: IVETT KOVACS",
            8,
            453.27,
            294.66,
            17.57,
            color="#285179",
            bold=True,
        ),
        text(
            "#WOW2020  |  WEEK 29  |  INTERMEDIATE",
            302.66,
            453.27,
            294.68,
            17.57,
            color="#285179",
            bold=True,
            align="1",
        ),
        text(
            "RECREATED BY : DONNA COLES",
            597.34,
            453.27,
            294.66,
            17.57,
            color="#285179",
            bold=True,
            align="2",
        ),
        text(
            "http://www.workout-wednesday.com/2020w29/",
            8,
            470.84,
            884,
            21.16,
            color="#0000ff",
            align="1",
        ),
    ]
    for zone in zones:
        if zone["type"] != "empty":
            zone["style"] = {"margin": 4}
    editor.add_dashboard(
        DASHBOARD,
        width=900,
        height=500,
        worksheet_names=[SHEET],
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"margin": 8},
            "children": zones,
        },
    )
    for field in ("Month", "Year"):
        editor.add_dashboard_set_action(
            DASHBOARD,
            SHEET,
            f"Hover {field} Set",
            event_type="on-hover",
            caption=f"Hover {field}",
            clear_option="exclude-all",
            selection_mode="assign",
        )
    editor.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(exist_ok=True)
    editor.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
