"""Rebuild profitability polygons and native expand set action from locked data."""

from pathlib import Path
from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_05_27_WW22_Profitability_Polygon v2"


def build(output_path=None):
    e = TWBEditor("")
    e.set_hyper_connection(str(next((HERE / "inputs").glob("*.hyper"))))
    e.add_set("Selected Sub-Cats", "Sub-Category", members=[])
    fields = [
        (
            "Path",
            "IF [Table Name]='WW' THEN 1 ELSEIF [Table Name]='WW1' THEN 2 ELSE 3 END",
            "integer",
            "dimension",
            "ordinal",
        ),
        ("x", "IF [Path]=1 THEN 0 ELSE 20 END", "integer", "measure", "quantitative"),
        ("Plot x", "FLOAT(MIN([x]))", "real", "measure", "quantitative"),
        (
            "y",
            "IF MIN([Path])=1 THEN AVG([Review]) ELSEIF MIN([Path])=2 THEN AVG([Revenue])/20 ELSE AVG([Budget])/20 END",
            "real",
            "measure",
            "quantitative",
        ),
        (
            "y2",
            "IF MIN([Path])=1 THEN AVG([Review]) ELSEIF MIN([Path])=2 THEN AVG([Revenue])/20 END",
            "real",
            "measure",
            "quantitative",
        ),
        ("Profit", "AVG([Revenue])-AVG([Budget])", "real", "measure", "quantitative"),
        ("Margin", "[Profit]/AVG([Budget])", "real", "measure", "quantitative"),
        (
            "Colour : Line",
            "IF [Profit]<0 THEN 'Non-Profitable' ELSE 'Profitable' END",
            "string",
            "measure",
            "nominal",
        ),
        (
            "Expand",
            "IF [Selected Sub-Cats] THEN [Sub-Category] ELSE 'Click to Expand' END",
            "string",
            "dimension",
            "nominal",
        ),
        (
            "Label:SubCat",
            "IF [Selected Sub-Cats] THEN '' ELSE [Sub-Category] END",
            "string",
            "dimension",
            "nominal",
        ),
        ("Zero", "MIN(0)", "integer", "measure", "quantitative"),
    ]
    for name, formula, datatype, role, field_type in fields:
        e.add_calculated_field(
            name, formula, datatype=datatype, role=role, field_type=field_type
        )
    e.add_calculated_field(
        "Review Label",
        "STR(AVG([Review]))",
        datatype="string",
        role="measure",
        field_type="nominal",
    )
    e.set_field_format("Profit", 'c"$"#,##0;-"$"#,##0')
    e.set_field_format("Margin", "p0.0%")
    e.set_field_format("Review", "#,##0.#")
    e.set_datasource_color_palette(
        "Colour : Line", {"Non-Profitable": "#ff6b6b", "Profitable": "#888888"}
    )
    for name in ["Data", "Legend", "Legend2", "Viz (2)"]:
        e.add_worksheet(name)
    for name in ["Legend", "Viz (2)"]:
        columns = (
            ["Sub-Category", "Plot x"] if name == "Legend" else ["Expand", "Plot x"]
        )
        e.configure_layered_chart(
            name,
            columns=columns,
            rows=["y", "y2"],
            panes=[
                {
                    "axis": "y",
                    "mark_type": "Polygon",
                    "detail": "Sub-Category",
                    "path": "Path",
                    "tooltip": ["Profit", "Margin"],
                    "mark_style": {"mark-color": "#666666", "mark-transparency": "78"},
                },
                {
                    "axis": "y2",
                    "mark_type": "Line",
                    "color": "Colour : Line",
                    "detail": "Sub-Category",
                    "path": "Path",
                    "label": "Review Label",
                    "label_runs": [
                        {"field": "Label:SubCat", "fontsize": 8},
                        {"text": "\n"},
                        {"field": "Review Label", "fontsize": 8},
                    ]
                    if name == "Viz (2)"
                    else [{"text": "Avg Review", "fontsize": 8}],
                    "labels": ["Label:SubCat"] if name == "Viz (2)" else [],
                    "tooltip": ["Profit", "Margin"],
                    "mark_style": {
                        "mark-line-markers": "all",
                        "size": "0.5",
                        "mark-labels-show": "true",
                        "mark-labels-cull": "true",
                    },
                },
            ],
            filters=[{"column": "Sub-Category", "values": ["Chairs"]}]
            if name == "Legend"
            else None,
        )
        e.configure_worksheet_style(
            name,
            background_color="#f5f5f5" if name == "Legend" else "#ffffff",
            hide_row_label="Sub-Category" if name == "Legend" else None,
            hide_col_field_labels=True,
            hide_row_field_labels=True,
            hide_sort_controls=True,
            hide_gridlines=True,
            hide_zeroline=True,
            hide_table_dividers=True,
            axis_style={
                "encodings": [
                    {
                        "field": "y",
                        "scope": "rows",
                        "type": "space",
                        "attr": "space",
                        "class": "0",
                        "field-type": "quantitative",
                        "range-type": "fixed",
                        "min": 1 if name == "Legend" else 0.5,
                        "max": 4.5 if name == "Legend" else 5.25,
                        "major-show": "false",
                        "minor-show": "false",
                    },
                    {
                        "field": "y2",
                        "scope": "rows",
                        "type": "space",
                        "attr": "space",
                        "class": "0",
                        "field-type": "quantitative",
                        "fold": "true",
                        "synchronized": "true",
                    },
                    {
                        "field": "Plot x",
                        "scope": "cols",
                        "type": "space",
                        "attr": "space",
                        "class": "0",
                        "field-type": "quantitative",
                        "range-type": "fixed",
                        "min": -0.5 if name == "Legend" else -0.3,
                        "max": 19.5 if name == "Legend" else 19.9,
                    },
                ],
                "per_field": [
                    {
                        "field": "Plot x",
                        "scope": "cols",
                        "attr": "display",
                        "value": "false",
                    },
                    {
                        "field": "y2",
                        "scope": "rows",
                        "attr": "display",
                        "value": "false",
                    },
                    {
                        "field": "y",
                        "scope": "rows",
                        "attr": "title",
                        "value": "Avg REVIEW",
                    },
                    {
                        "field": "y",
                        "scope": "rows",
                        "attr": "display",
                        "value": "false" if name == "Legend" else "true",
                    },
                ],
            },
        )
    e.configure_chart(
        "Legend2",
        mark_type="Circle",
        rows=["Sub-Category"],
        columns=["Zero"],
        color="Colour : Line",
        label="Colour : Line",
        mark_sizing_off=True,
        filters=[{"column": "Sub-Category", "values": ["Labels", "Tables"]}],
    )
    e.configure_worksheet_style(
        "Legend2",
        hide_axes=True,
        hide_row_label="Sub-Category",
        hide_row_field_labels=True,
        hide_col_field_labels=True,
        hide_table_dividers=True,
        background_color="#f5f5f5",
        pane_mark_style={"size": "0.3", "mark-labels-show": "true"},
        axis_style={
            "encodings": [
                {
                    "field": "Zero",
                    "scope": "cols",
                    "type": "space",
                    "attr": "space",
                    "class": "0",
                    "field-type": "quantitative",
                    "range-type": "fixed",
                    "min": -1,
                    "max": 9,
                }
            ]
        },
    )
    e.configure_chart(
        "Data",
        mark_type="Text",
        rows=["Sub-Category", "Table Name", "Path", "Colour : Line"],
        measure_values=["AVG(Review)", "AVG(Budget)", "AVG(Revenue)", "MIN(x)", "y"],
    )

    def p(x, y, w, h):
        return {
            "x": round(x / 1000 * 100000),
            "y": round(y / 700 * 100000),
            "w": round(w / 1000 * 100000),
            "h": round(h / 700 * 100000),
        }

    zones = [
        {
            "type": "text",
            "runs": [
                {
                    "text": "Profitability",
                    "font_size": 16,
                    "bold": True,
                    "font_alignment": "0",
                }
            ],
            "absolute": p(36, 88, 278, 36),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "Is your budget recovered?",
                    "font_size": 10,
                    "font_alignment": "0",
                }
            ],
            "absolute": p(36, 124, 278, 28),
        },
        {
            "type": "text",
            "runs": [
                {
                    "text": "How to read it",
                    "font_size": 12,
                    "font_alignment": "0",
                    "font_color": "#666666",
                }
            ],
            "absolute": p(36, 200, 249, 35),
        },
        {
            "type": "worksheet",
            "name": "Legend",
            "show_title": False,
            "fit": "entire",
            "absolute": p(36, 235, 249, 238),
        },
        {
            "type": "worksheet",
            "name": "Viz (2)",
            "show_title": False,
            "fit": "entire",
            "absolute": p(309, 79, 580, 517),
        },
        {
            "type": "worksheet",
            "name": "Legend2",
            "show_title": False,
            "fit": "entire",
            "absolute": p(0, 499, 270, 70),
        },
    ]
    for text, x, y, w, h in [
        ("REVENUE", 890, 84, 100, 30),
        ("BUDGET", 891, 565, 100, 30),
        ("DESIGNED BY : @IvettAlexa", 8, 631, 328, 32),
        ("#WOW2020 | WEEK 22", 336, 631, 328, 32),
        ("RECREATED WITH CWTWB", 664, 631, 328, 32),
        ("http://www.workout-wednesday.com/2020w22/", 8, 663, 984, 29),
    ]:
        zones.append(
            {
                "type": "text",
                "runs": [
                    {
                        "text": text,
                        "font_size": 8,
                        "font_color": "#333333",
                        "font_alignment": "1",
                    }
                ],
                "absolute": p(x, y, w, h),
            }
        )
    for zone in zones:
        if zone["type"] == "text":
            zone["style"] = {"background-color": "#f5f5f5"}
    e.add_dashboard(
        DASHBOARD,
        width=1000,
        height=700,
        worksheet_names=["Legend", "Viz (2)", "Legend2"],
        layout={
            "type": "container",
            "direction": "floating",
            "style": {"background-color": "#f5f5f5"},
            "children": zones,
        },
    )
    e.add_dashboard_set_action(
        DASHBOARD,
        "Viz (2)",
        "Selected Sub-Cats",
        event_type="on-select",
        caption="Set1",
        clear_option="exclude-all",
        selection_mode="add",
    )
    e.set_active_dashboard(DASHBOARD)
    output = Path(output_path or HERE / "outputs/replicated-workbook.twbx")
    output.parent.mkdir(exist_ok=True)
    e.save(output, validate=False)
    return output


if __name__ == "__main__":
    print(build())
