"""Build independent monthly pipeline and blended targets from locked extracts."""

from pathlib import Path

from cwtwb import TWBEditor

HERE = Path(__file__).resolve().parent
DASHBOARD = "2020_04_15_Pipeline_V_AdjustedTarget"


def build():
    e = TWBEditor("")
    e.set_hyper_connection(
        str(HERE / "inputs/Pipeline (2020_04_15_WW16_Sales Pipeline).hyper")
    )
    primary = e.select_datasource("Sample _ Superstore (Simple)")
    secondary = e.add_hyper_datasource(
        "Monthly Target",
        str(HERE / "inputs/Monthly Target (2020_04_15_WW16_Sales Pipeline).hyper"),
    )
    e.add_calculated_field(
        "BLEND - Month",
        "[Date]",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.select_datasource(primary)
    e.add_calculated_field(
        "BLEND - Month",
        "DATE(DATETRUNC('month',[Closed Date]))",
        datatype="date",
        role="dimension",
        field_type="ordinal",
    )
    e.import_blended_field("Target", secondary, "SUM(Target)")
    specs = [
        ("Today", "#2020-04-15#", "date", "dimension", "ordinal", False),
        (
            "Closed Won",
            "ZN(IF [Stage]='Closed Won' THEN [Sales] END)",
            "real",
            "measure",
            "quantitative",
            False,
        ),
        (
            "Pipeline",
            "IF [Stage]='Negotiating' OR [Stage]='Proposing' THEN [Sales] END",
            "real",
            "measure",
            "quantitative",
            False,
        ),
        (
            "YTD Closed",
            "WINDOW_SUM(SUM(IF [Closed Date]<DATETRUNC('month',[Today]) THEN [Closed Won] END))",
            "real",
            "measure",
            "quantitative",
            True,
        ),
        (
            "YTD Target",
            "WINDOW_SUM(IF MIN([Closed Date])<DATETRUNC('month',[Today]) THEN [Target] END)",
            "real",
            "measure",
            "quantitative",
            True,
        ),
        (
            "Missed Sales Value",
            "[YTD Target]-[YTD Closed]",
            "real",
            "measure",
            "quantitative",
            True,
        ),
        (
            "Remaining Months",
            "12-DATEPART('month',[Today])+1",
            "integer",
            "dimension",
            "ordinal",
            False,
        ),
        (
            "Distributed Missed Sales Value",
            "[Missed Sales Value]/MIN([Remaining Months])",
            "real",
            "measure",
            "quantitative",
            True,
        ),
        (
            "Adjusted Target",
            "IF DATETRUNC('month',MIN([Closed Date]))>=DATETRUNC('month',[Today]) THEN [Target]+[Distributed Missed Sales Value] END",
            "real",
            "measure",
            "quantitative",
            True,
        ),
        (
            "Missing Pipeline",
            "IF ZN(SUM([Pipeline]))=0 THEN NULL ELSEIF DATETRUNC('month',MIN([Closed Date]))=DATETRUNC('month',[Today]) THEN IF SUM([Closed Won])+SUM([Pipeline])<[Adjusted Target] THEN ZN([Adjusted Target]-SUM([Closed Won])-SUM([Pipeline])) END ELSEIF SUM([Pipeline])<[Adjusted Target] THEN ZN([Adjusted Target]-SUM([Pipeline])) ELSE 0 END",
            "real",
            "measure",
            "quantitative",
            True,
        ),
    ]
    for name, formula, datatype, role, field_type, table_calc in specs:
        e.add_calculated_field(
            name,
            formula,
            datatype=datatype,
            role=role,
            field_type=field_type,
            **({"table_calc": "Rows"} if table_calc else {}),
        )
        if role == "measure":
            e.set_field_format(name, 'c"$"#,##0;-"$"#,##0')
    e.add_calculated_field(
        "Current Year",
        "YEAR([Closed Date])=YEAR([Today])",
        datatype="boolean",
        role="dimension",
        field_type="nominal",
    )
    filters = [{"column": "Current Year", "values": [True]}]
    e.set_field_format("Target", 'c"$"#,##0;-"$"#,##0')
    metrics = [
        "Closed Won",
        "Pipeline",
        "Target",
        "YTD Closed",
        "YTD Target",
        "Missed Sales Value",
        "Distributed Missed Sales Value",
        "Adjusted Target",
        "Missing Pipeline",
    ]
    e.add_worksheet("Data")
    e.configure_chart(
        "Data",
        mark_type="Text",
        columns=["MONTH(Closed Date)"],
        label="Target",
        tooltip=metrics,
        filters=filters,
    )
    e.configure_datasource_blend(
        "Data",
        secondary,
        link_fields={"BLEND - Month": "BLEND - Month"},
        secondary_fields=["SUM(Target)"],
    )
    e.add_worksheet("Viz")
    e.configure_layered_chart(
        "Viz",
        columns=["MONTH(Closed Date)"],
        rows=["Multiple Values", "Target"],
        panes=[
            {
                "mark_type": "Bar",
                "axis": "Multiple Values",
                "measure_values": ["Missing Pipeline", "Pipeline", "Closed Won"],
                "color": "Measure Names",
                "color_map": {
                    "Closed Won": "#76b7b2",
                    "Pipeline": "#b07aa1",
                    "Missing Pipeline": "#bab0ac",
                },
                "tooltip": metrics,
            },
            {
                "mark_type": "GanttBar",
                "axis": "Target",
                "mark_style": {
                    "mark-color": "#000000",
                    "size": "1.9780110121",
                    "has-stroke": "true",
                    "stroke-color": "#000000",
                },
                "mark_sizing_off": True,
                "tooltip": metrics,
            },
        ],
        axis_shelf="rows",
        synchronized=True,
        fold_axes=True,
        filters=filters,
    )
    e.configure_datasource_blend(
        "Viz",
        secondary,
        link_fields={"BLEND - Month": "BLEND - Month"},
        secondary_fields=["SUM(Target)"],
    )
    reference = e.add_reference_line(
        "Viz",
        axis_field="Target",
        value_field="Adjusted Target",
        scope="per-cell",
        formula="average",
        label_type="none",
        tooltip="Adjusted Target (Dashed) : <Value>",
        pane_index=0,
    )
    e.configure_reference_line_style(
        "Viz",
        reference.split("'")[1],
        {"line-pattern-only": "dotted", "stroke-color": "#000000", "stroke-size": "3"},
    )
    e.configure_worksheet_style(
        "Viz",
        hide_gridlines=True,
        hide_zeroline=True,
        hide_borders=True,
        hide_table_dividers=True,
        hide_col_field_labels=True,
        hide_row_field_labels=True,
        hide_sort_controls=True,
        pane_mark_style={"mark-labels-show": "false"},
        axis_style={
            "per_field": [
                {
                    "field": "Target",
                    "attr": "display",
                    "value": "false",
                    "scope": "rows",
                },
                {
                    "field": "Multiple Values",
                    "attr": "title",
                    "value": "",
                    "scope": "rows",
                },
            ]
        },
        label_formats=[{"field": "MONTH(Closed Date)", "text-format": "*mmm"}],
    )
    e.set_worksheet_title("Viz", "")

    def zone(kind, x, y, w, h, **options):
        return {
            "type": kind,
            "absolute": {
                "x": round(x / 800 * 100000),
                "y": round(y / 600 * 100000),
                "w": round(w / 800 * 100000),
                "h": round(h / 600 * 100000),
            },
            **options,
        }

    e.add_dashboard(
        DASHBOARD,
        width=800,
        height=600,
        layout={
            "type": "container",
            "direction": "floating",
            "children": [
                zone(
                    "text",
                    8,
                    8,
                    784,
                    58,
                    text="Growth Planning : Actual v Target",
                    runs=[
                        {
                            "text": "Growth Planning : Actual v Target",
                            "font_size": "15",
                            "font_color": "#000000",
                            "font_alignment": "0",
                        }
                    ],
                    font_size="15",
                    font_color="#000000",
                ),
                zone(
                    "text",
                    8,
                    68,
                    784,
                    38,
                    text="■ Closed Won    ■ Pipeline    ■ Missing Pipeline     ━ Target     ┄ Adjusted Target",
                    runs=[
                        {
                            "text": "■ Closed Won   ",
                            "font_color": "#76b7b2",
                            "font_size": "10",
                        },
                        {
                            "text": "■ Pipeline   ",
                            "font_color": "#b07aa1",
                            "font_size": "10",
                        },
                        {
                            "text": "■ Missing Pipeline   ",
                            "font_color": "#bab0ac",
                            "font_size": "10",
                        },
                        {
                            "text": "━ Target   ┄ Adjusted Target",
                            "font_color": "#000000",
                            "font_size": "10",
                        },
                    ],
                ),
                zone(
                    "worksheet",
                    8,
                    112,
                    784,
                    410,
                    name="Viz",
                    fit="entire",
                    show_title=False,
                ),
                zone(
                    "text",
                    8,
                    536,
                    784,
                    24,
                    text="DESIGNED BY : LORNA BROWN | #WOW2020 WEEK 16 | RECREATED WITH CWTWB",
                    font_size="8",
                ),
                zone(
                    "text",
                    8,
                    568,
                    784,
                    24,
                    text="https://www.workout-wednesday.com/2020w16/",
                    font_size="8",
                    font_color="#006080",
                ),
            ],
        },
    )
    output = HERE / "outputs/replicated-workbook.twbx"
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
